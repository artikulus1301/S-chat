from flask_socketio import Namespace, emit, join_room, leave_room
from flask import request
from app import db
from app.models import User, Chat, ChatMember, Message
import json

class ChatNamespace(Namespace):
    def on_connect(self):
        """Handle client connection"""
        print(f"Client connected: {request.sid}")
        emit('connected', {'status': 'connected', 'sid': request.sid})
    
    def on_disconnect(self):
        """Handle client disconnect"""
        print(f"Client disconnected: {request.sid}")
    
    def on_join_chat(self, data):
        """Join a chat room"""
        try:
            chat_id = data.get('chat_id')
            user_id = data.get('user_id')
            
            # Verify user is member of chat
            membership = ChatMember.query.filter_by(
                user_id=user_id, chat_id=chat_id
            ).first()
            
            if membership:
                room = f"chat_{chat_id}"
                join_room(room)
                emit('join_success', {'chat_id': chat_id, 'room': room})
            else:
                emit('error', {'message': 'Not a member of this chat'})
                
        except Exception as e:
            emit('error', {'message': str(e)})
    
    def on_send_message(self, data):
        """Send encrypted message to chat"""
        try:
            chat_id = data.get('chat_id')
            user_id = data.get('user_id')
            encrypted_content = data.get('content')
            message_type = data.get('type', 'text')
            
            # Create message record
            message = Message(
                chat_id=chat_id,
                user_id=user_id,
                content=encrypted_content,
                message_type=message_type
            )
            
            db.session.add(message)
            db.session.commit()
            
            # Broadcast to chat room
            room = f"chat_{chat_id}"
            emit('new_message', {
                'id': message.id,
                'chat_id': chat_id,
                'user_id': user_id,
                'content': encrypted_content,
                'type': message_type,
                'timestamp': message.timestamp.isoformat()
            }, room=room)
            
        except Exception as e:
            emit('error', {'message': str(e)})
    
    def on_typing(self, data):
        """Handle typing indicators"""
        chat_id = data.get('chat_id')
        user_id = data.get('user_id')
        is_typing = data.get('is_typing', False)
        
        room = f"chat_{chat_id}"
        emit('user_typing', {
            'user_id': user_id,
            'is_typing': is_typing
        }, room=room, include_self=False)