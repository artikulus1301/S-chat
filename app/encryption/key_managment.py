import os
import json
import base64
from app import db
from app.models import User
from .signal_protocol import SignalProtocol

class KeyManager:
    def __init__(self, store_path):
        self.signal = SignalProtocol(store_path)
        self.store_path = store_path
    
    def setup_user_keys(self, user_id):
        """Setup encryption keys for a new user"""
        try:
            user = User.query.get(user_id)
            if not user:
                raise ValueError("User not found")
            
            # Generate keys if not already set
            if not user.identity_key_public:
                identity_keys = self.signal.generate_identity_key_pair()
                signed_pre_key = self.signal.generate_signed_pre_key(
                    self.signal._deserialize_private_key(identity_keys['private'])
                )
                
                # Store keys in user record
                user.identity_key_public = identity_keys['public']
                user.identity_key_private = identity_keys['private']
                user.signed_pre_key_public = signed_pre_key['public']
                user.signed_pre_key_private = signed_pre_key['private']
                user.signed_pre_key_signature = signed_pre_key['signature']
                
                db.session.commit()
            
            return self.get_pre_key_bundle(user_id)
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def get_pre_key_bundle(self, user_id):
        """Get pre-key bundle for a user (for establishing session)"""
        user = User.query.get(user_id)
        if not user:
            return None
        
        return {
            'identity_key': user.identity_key_public,
            'signed_pre_key': {
                'key_id': 1,  # In real implementation, manage key IDs
                'public_key': user.signed_pre_key_public,
                'signature': user.signed_pre_key_signature
            },
            'registration_id': 1,  # Simple implementation
            'device_id': 1
        }
    
    def encrypt_message(self, sender_id, recipient_id, message):
        """Encrypt message for recipient"""
        # This is a simplified implementation
        # In production, use proper Signal Protocol session management
        
        # For demo purposes, we'll use a simple base64 encoding
        # REPLACE THIS WITH ACTUAL SIGNAL PROTOCOL ENCRYPTION
        encoded_message = base64.b64encode(message.encode()).decode()
        
        return {
            'ciphertext': encoded_message,
            'type': 'signal',
            'sender_id': sender_id,
            'recipient_id': recipient_id
        }
    
    def decrypt_message(self, recipient_id, encrypted_message):
        """Decrypt message for recipient"""
        # This is a simplified implementation
        # In production, use proper Signal Protocol session management
        
        if encrypted_message.get('type') != 'signal':
            raise ValueError("Unsupported encryption type")
        
        # For demo purposes, we'll use simple base64 decoding
        # REPLACE THIS WITH ACTUAL SIGNAL PROTOCOL DECRYPTION
        decoded_message = base64.b64decode(encrypted_message['ciphertext']).decode()
        
        return decoded_message
    
    def rotate_signed_pre_key(self, user_id):
        """Rotate signed pre-key for enhanced security"""
        try:
            user = User.query.get(user_id)
            if not user:
                return False
            
            identity_private_key = self.signal._deserialize_private_key(
                user.identity_key_private
            )
            
            new_signed_pre_key = self.signal.generate_signed_pre_key(identity_private_key)
            
            user.signed_pre_key_public = new_signed_pre_key['public']
            user.signed_pre_key_private = new_signed_pre_key['private']
            user.signed_pre_key_signature = new_signed_pre_key['signature']
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            return False