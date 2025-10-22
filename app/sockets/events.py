from flask_socketio import emit, join_room, leave_room
from app import db
from app.models import Message, ChatMember
import json

def handle_typing(data):
    """Handle typing indicators"""
    chat_id = data.get('chat_id')
    user_id = data.get('user_id')
    is_typing = data.get('is_typing', False)
    
    room = f"chat_{chat_id}"
    emit('user_typing', {
        'user_id': user_id,
        'is_typing': is_typing
    }, room=room, include_self=False)

def handle_message_read(data):
    """Handle message read receipts"""
    chat_id = data.get('chat_id')
    user_id = data.get('user_id')
    message_id = data.get('message_id')
    
    room = f"chat_{chat_id}"
    emit('message_read', {
        'message_id': message_id,
        'user_id': user_id,
        'timestamp': datetime.utcnow().isoformat()
    }, room=room)

def handle_user_online(data):
    """Handle user online status"""
    user_id = data.get('user_id')
    is_online = data.get('is_online', True)
    
    # Get all chats where user is member
    user_chats = ChatMember.query.filter_by(user_id=user_id).all()
    
    for chat_member in user_chats:
        room = f"chat_{chat_member.chat_id}"
        emit('user_status', {
            'user_id': user_id,
            'is_online': is_online,
            'timestamp': datetime.utcnow().isoformat()
        }, room=room)