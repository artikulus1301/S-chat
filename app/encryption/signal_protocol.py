import os
import json
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import x25519, ed25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend
import base64

class SignalProtocol:
    def __init__(self, store_path):
        self.store_path = store_path
        os.makedirs(store_path, exist_ok=True)
    
    def generate_identity_key_pair(self):
        """Generate X25519 identity key pair for key exchange"""
        private_key = x25519.X25519PrivateKey.generate()
        public_key = private_key.public_key()
        
        return {
            'private': self._serialize_private_key(private_key),
            'public': self._serialize_public_key(public_key)
        }
    
    def generate_signing_key_pair(self):
        """Generate Ed25519 key pair for signing"""
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        
        return {
            'private': self._serialize_ed25519_private_key(private_key),
            'public': self._serialize_ed25519_public_key(public_key)
        }
    
    def generate_signed_pre_key(self, signing_private_key):
        """Generate signed pre-key with Ed25519 signature"""
        # Генерируем X25519 пре-ключ
        pre_key_private = x25519.X25519PrivateKey.generate()
        pre_key_public = pre_key_private.public_key()
        
        # Сериализуем публичный ключ для подписи
        pre_key_public_bytes = pre_key_public.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        
        # Подписываем Ed25519 ключом
        signature = signing_private_key.sign(pre_key_public_bytes)
        
        return {
            'key_id': os.urandom(4).hex(),
            'private': self._serialize_private_key(pre_key_private),
            'public': self._serialize_public_key(pre_key_public),
            'signature': base64.b64encode(signature).decode()
        }
    
    def generate_pre_keys(self, start_id=1, count=100):
        """Generate one-time pre-keys"""
        pre_keys = []
        for i in range(start_id, start_id + count):
            private_key = x25519.X25519PrivateKey.generate()
            public_key = private_key.public_key()
            
            pre_keys.append({
                'key_id': i,
                'private': self._serialize_private_key(private_key),
                'public': self._serialize_public_key(public_key)
            })
        
        return pre_keys
    
    def _serialize_private_key(self, private_key):
        return base64.b64encode(
            private_key.private_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PrivateFormat.Raw,
                encryption_algorithm=serialization.NoEncryption()
            )
        ).decode()
    
    def _serialize_public_key(self, public_key):
        return base64.b64encode(
            public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            )
        ).decode()
    
    def _serialize_ed25519_private_key(self, private_key):
        return base64.b64encode(
            private_key.private_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PrivateFormat.Raw,
                encryption_algorithm=serialization.NoEncryption()
            )
        ).decode()
    
    def _serialize_ed25519_public_key(self, public_key):
        return base64.b64encode(
            public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            )
        ).decode()
    
    def _deserialize_private_key(self, key_str):
        return x25519.X25519PrivateKey.from_private_bytes(
            base64.b64decode(key_str)
        )
    
    def _deserialize_public_key(self, key_str):
        return x25519.X25519PublicKey.from_public_bytes(
            base64.b64decode(key_str)
        )
    
    def _deserialize_ed25519_private_key(self, key_str):
        return ed25519.Ed25519PrivateKey.from_private_bytes(
            base64.b64decode(key_str)
        )