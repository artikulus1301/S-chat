from app import db
from datetime import datetime, timedelta
import secrets
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

    # Верификация
    email_verified = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)  # ✅ Добавлено для совместимости с диагностикой
    verification_token = db.Column(db.String(100), unique=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Пароль
    password_hash = db.Column(db.String(255), nullable=False)

    # Сброс пароля
    reset_token = db.Column(db.String(100), unique=True, nullable=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)

    # Ключи шифрования
    identity_key_public = db.Column(db.Text)
    identity_key_private = db.Column(db.Text, nullable=True)  # зашифрованный
    signing_key_public = db.Column(db.Text)
    signing_key_private = db.Column(db.Text, nullable=True)
    signed_pre_key_public = db.Column(db.Text)
    signed_pre_key_private = db.Column(db.Text, nullable=True)
    signed_pre_key_signature = db.Column(db.Text)

    # Отношения
    messages = db.relationship('Message', backref='author', lazy=True)
    chat_memberships = db.relationship('ChatMember', backref='user', lazy=True)

    # Методы -------------------------------------------------------------

    def set_password(self, password):
        """Установка хешированного пароля"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Проверка пароля"""
        return check_password_hash(self.password_hash, password)

    def generate_verification_token(self):
        """Генерация токена для подтверждения email"""
        self.verification_token = secrets.token_urlsafe(32)
        return self.verification_token

    def generate_password_reset_token(self):
        """Генерация токена для сброса пароля"""
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        return self.reset_token

    def is_reset_token_valid(self):
        """Проверка валидности токена сброса"""
        return (
            self.reset_token
            and self.reset_token_expires
            and datetime.utcnow() < self.reset_token_expires
        )

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f'<User {self.username}>'


class Chat(db.Model):
    __tablename__ = 'chat'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    is_group = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Отношения
    members = db.relationship('ChatMember', backref='chat', lazy=True, cascade='all, delete-orphan')
    messages = db.relationship('Message', backref='chat', lazy=True, cascade='all, delete-orphan')


class ChatMember(db.Model):
    __tablename__ = 'chat_member'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)

    __table_args__ = (db.UniqueConstraint('user_id', 'chat_id', name='unique_chat_member'),)


class Message(db.Model):
    __tablename__ = 'message'

    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text)  # зашифрованное содержимое
    message_type = db.Column(db.String(20), default='text')  # text, image, audio, file
    file_path = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Signal Protocol
    registration_id = db.Column(db.Integer)
    device_id = db.Column(db.Integer)
    pre_key_bundle = db.Column(db.Text)  # сериализованный пакет pre-key
