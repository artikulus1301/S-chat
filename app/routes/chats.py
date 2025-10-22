from flask import Blueprint, request, jsonify
from app import db
from app.models import Chat, ChatMember, User, Message
from flask_login import login_required, current_user

chats_bp = Blueprint('chats', __name__)

@chats_bp.route('/chats', methods=['GET'])
def get_user_chats():
    """Get all chats for a user"""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        # Get user's chat memberships
        memberships = ChatMember.query.filter_by(user_id=user_id).all()
        
        chats_data = []
        for membership in memberships:
            chat = Chat.query.get(membership.chat_id)
            
            # Get last message
            last_message = Message.query.filter_by(chat_id=chat.id)\
                .order_by(Message.timestamp.desc()).first()
            
            # Get member count
            member_count = ChatMember.query.filter_by(chat_id=chat.id).count()
            
            chats_data.append({
                'id': chat.id,
                'name': chat.name,
                'is_group': chat.is_group,
                'member_count': member_count,
                'last_message': {
                    'content': last_message.content if last_message else None,
                    'timestamp': last_message.timestamp.isoformat() if last_message else None,
                    'type': last_message.message_type if last_message else 'text'
                } if last_message else None,
                'created_at': chat.created_at.isoformat()
            })
        
        return jsonify({'chats': chats_data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chats_bp.route('/chats', methods=['POST'])
def create_chat():
    """Create a new chat (individual or group)"""
    try:
        data = request.get_json()
        name = data.get('name')
        user_ids = data.get('user_ids', [])  # List of user IDs to add to chat
        created_by = data.get('created_by')
        is_group = data.get('is_group', False)
        
        if not created_by:
            return jsonify({'error': 'Creator user ID is required'}), 400
        
        # For individual chats, ensure exactly 2 users
        if not is_group and len(user_ids) != 1:
            return jsonify({'error': 'Individual chat must have exactly 2 users'}), 400
        
        # For group chats, check max members
        if is_group and len(user_ids) + 1 > 50:  # +1 for creator
            return jsonify({'error': 'Group chat cannot exceed 50 members'}), 400
        
        # Create chat
        chat = Chat(
            name=name,
            is_group=is_group,
            created_by=created_by
        )
        
        db.session.add(chat)
        db.session.flush()  # Get chat ID without committing
        
        # Add creator as admin
        creator_member = ChatMember(
            user_id=created_by,
            chat_id=chat.id,
            is_admin=True
        )
        db.session.add(creator_member)
        
        # Add other users
        for user_id in user_ids:
            if user_id != created_by:  # Don't add creator twice
                member = ChatMember(
                    user_id=user_id,
                    chat_id=chat.id,
                    is_admin=False
                )
                db.session.add(member)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Chat created successfully',
            'chat_id': chat.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@chats_bp.route('/chats/<int:chat_id>/messages', methods=['GET'])
def get_chat_messages(chat_id):
    """Get messages for a specific chat"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        messages = Message.query.filter_by(chat_id=chat_id)\
            .order_by(Message.timestamp.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        messages_data = []
        for message in messages.items:
            messages_data.append({
                'id': message.id,
                'user_id': message.user_id,
                'content': message.content,
                'type': message.message_type,
                'file_path': message.file_path,
                'timestamp': message.timestamp.isoformat()
            })
        
        return jsonify({
            'messages': messages_data,
            'total': messages.total,
            'pages': messages.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chats_bp.route('/chats/<int:chat_id>/members', methods=['GET'])
def get_chat_members(chat_id):
    """Get members of a specific chat"""
    try:
        members = ChatMember.query.filter_by(chat_id=chat_id).all()
        
        members_data = []
        for member in members:
            user = User.query.get(member.user_id)
            members_data.append({
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'is_admin': member.is_admin,
                'joined_at': member.joined_at.isoformat()
            })
        
        return jsonify({'members': members_data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chats_bp.route('/chats/<int:chat_id>/invite', methods=['POST'])
def invite_to_chat():
    """Invite users to a group chat"""
    try:
        data = request.get_json()
        chat_id = data.get('chat_id')
        user_ids = data.get('user_ids', [])
        invited_by = data.get('invited_by')
        
        chat = Chat.query.get(chat_id)
        if not chat:
            return jsonify({'error': 'Chat not found'}), 404
        
        if not chat.is_group:
            return jsonify({'error': 'Can only invite to group chats'}), 400
        
        # Check if inviter is admin
        inviter_member = ChatMember.query.filter_by(
            user_id=invited_by, 
            chat_id=chat_id
        ).first()
        
        if not inviter_member or not inviter_member.is_admin:
            return jsonify({'error': 'Only admins can invite users'}), 403
        
        # Check member limit
        current_members = ChatMember.query.filter_by(chat_id=chat_id).count()
        if current_members + len(user_ids) > 50:
            return jsonify({'error': 'Cannot exceed 50 members'}), 400
        
        # Add users to chat
        for user_id in user_ids:
            # Check if user is already a member
            existing_member = ChatMember.query.filter_by(
                user_id=user_id, 
                chat_id=chat_id
            ).first()
            
            if not existing_member:
                member = ChatMember(
                    user_id=user_id,
                    chat_id=chat_id,
                    is_admin=False
                )
                db.session.add(member)
        
        db.session.commit()
        
        return jsonify({'message': 'Users invited successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500