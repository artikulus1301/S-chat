from flask import Blueprint, request, jsonify, current_app, render_template, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from app import db, mail
from app.models import User
from app.encryption.signal_protocol import SignalProtocol
from flask_mail import Message
import re
import logging

auth_bp = Blueprint('auth', __name__)

# HTML Pages
@auth_bp.route('/login-page', methods=['GET'])
def login_page():
    """HTML страница для логина"""
    return render_template('auth/login.html')

@auth_bp.route('/register-page', methods=['GET'])
def register_page():
    """HTML страница для регистрации"""
    return render_template('auth/register.html')

@auth_bp.route('/verify-page/<token>', methods=['GET'])
def verify_email_page(token):
    """HTML страница для верификации email"""
    user = User.query.filter_by(verification_token=token).first()
    if user:
        user.email_verified = True
        user.verification_token = None
        db.session.commit()
        return render_template('auth/verification_success.html')
    else:
        return render_template('auth/verification_failed.html')

@auth_bp.route('/')
def auth_index():
    """Главная страница auth blueprint"""
    return redirect(url_for('auth.login_page'))

def is_valid_email(email):
    """Проверка валидности email адреса"""
    if not email:
        return False
    
    # Исправленное регулярное выражение
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        # Проверяем JSON
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
            
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        email = data.get('email', '').strip().lower()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()  # 🟩 Добавили пароль
        
        if not email or not username or not password:
            return jsonify({'error': 'Email, username and password are required'}), 400
        
        # Проверка формата email
        if not is_valid_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Проверка длины username
        if len(username) < 3:
            return jsonify({'error': 'Username must be at least 3 characters long'}), 400
        
        if len(username) > 20:
            return jsonify({'error': 'Username must be less than 20 characters'}), 400
        
        # Проверка длины пароля
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
        # Проверка на дублирование
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already registered'}), 400
        
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already taken'}), 400
        
        # Генерация криптографических ключей
        signal = SignalProtocol(current_app.config['SIGNAL_PROTOCOL_STORE'])
        identity_keys = signal.generate_identity_key_pair()
        signing_keys = signal.generate_signing_key_pair()
        signing_private_key = signal._deserialize_ed25519_private_key(signing_keys['private'])
        signed_pre_key = signal.generate_signed_pre_key(signing_private_key)
        
        # Создание пользователя
        user = User(
            email=email,
            username=username,
            identity_key_public=identity_keys['public'],
            identity_key_private=identity_keys['private'],
            signing_key_public=signing_keys['public'],
            signing_key_private=signing_keys['private'],
            signed_pre_key_public=signed_pre_key['public'],
            signed_pre_key_private=signed_pre_key['private'],
            signed_pre_key_signature=signed_pre_key['signature']
        )
        
        # 🟩 Генерация хеша пароля
        user.set_password(password)
        
        # 🟩 Генерация токена верификации
        user.generate_verification_token()
        
        db.session.add(user)
        db.session.commit()
        
        # Отправка письма
        email_sent = send_verification_email(user)
        
        response_data = {
            'message': 'Registration successful.',
            'user_id': user.id,
            'email_sent': email_sent
        }
        
        if not email_sent:
            verification_url = f"{request.host_url}auth/verify-page/{user.verification_token}"
            response_data['verification_url'] = verification_url
            response_data['debug_info'] = 'Email not configured. Use the verification URL above.'
        
        return jsonify(response_data), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': 'Registration failed. Please try again.'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        # Проверяем JSON
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
            
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        email = data.get('email', '').strip().lower()
        username = data.get('username', '').strip()
        
        if not email and not username:
            return jsonify({'error': 'Email or username is required'}), 400
        
        # Find user by email or username
        if email:
            user = User.query.filter_by(email=email).first()
        else:
            user = User.query.filter_by(username=username).first()
        
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Check if email is verified
        if not user.email_verified:
            # Предлагаем отправить письмо повторно
            return jsonify({
                'error': 'Email not verified', 
                'can_resend': True,
                'email': user.email
            }), 403
        
        # Login user
        login_user(user, remember=True)
        
        return jsonify({
            'message': 'Login successful',
            'user_id': user.id,
            'username': user.username,
            'email': user.email
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Login failed. Please try again.'}), 500

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    try:
        logout_user()
        return jsonify({'message': 'Logout successful'}), 200
    except Exception as e:
        current_app.logger.error(f"Logout error: {str(e)}")
        return jsonify({'error': 'Logout failed'}), 500

@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    try:
        return jsonify({
            'user_id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'email_verified': current_user.email_verified
        }), 200
    except Exception as e:
        current_app.logger.error(f"Get user error: {str(e)}")
        return jsonify({'error': 'Failed to get user info'}), 500

@auth_bp.route('/verify/<token>')
def verify_email(token):
    try:
        user = User.query.filter_by(verification_token=token).first()
        if user:
            user.email_verified = True
            user.verification_token = None
            db.session.commit()
            return jsonify({'message': 'Email verified successfully'}), 200
        else:
            return jsonify({'error': 'Invalid verification token'}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Verify email error: {str(e)}")
        return jsonify({'error': 'Verification failed'}), 500

@auth_bp.route('/resend-verification', methods=['POST'])
def resend_verification():
    try:
        # Проверяем JSON
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
            
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user.email_verified:
            return jsonify({'error': 'Email already verified'}), 400
        
        user.generate_verification_token()
        db.session.commit()
        
        email_sent = send_verification_email(user)
        
        response_data = {
            'message': 'Verification email sent successfully' if email_sent else 'Verification prepared',
            'email_sent': email_sent
        }
        
        if not email_sent:
            verification_url = f"{request.host_url}auth/verify-page/{user.verification_token}"
            response_data['verification_url'] = verification_url
            response_data['debug_info'] = 'Email not configured. Use the verification URL above.'
        
        return jsonify(response_data), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Resend verification error: {str(e)}")
        return jsonify({'error': 'Failed to resend verification'}), 500

def send_verification_email(user):
    """
    Отправка verification email с обработкой различных сценариев
    """
    try:
        # Детальное логирование конфигурации
        logging.info("=== EMAIL CONFIGURATION CHECK ===")
        logging.info(f"MAIL_SERVER: {current_app.config.get('MAIL_SERVER')}")
        logging.info(f"MAIL_PORT: {current_app.config.get('MAIL_PORT')}")
        logging.info(f"MAIL_USERNAME: {current_app.config.get('MAIL_USERNAME')}")
        logging.info(f"MAIL_USE_TLS: {current_app.config.get('MAIL_USE_TLS')}")
        logging.info(f"MAIL_USE_SSL: {current_app.config.get('MAIL_USE_SSL')}")
        
        # Проверяем базовую конфигурацию email
        mail_username = current_app.config.get('MAIL_USERNAME')
        mail_password = current_app.config.get('MAIL_PASSWORD')
        
        if not mail_username or not mail_password:
            logging.warning("Email credentials not configured - using development mode")
            return send_verification_email_development(user)
        
        # Если конфигурация есть, пытаемся отправить настоящее письмо
        verification_url = f"{request.host_url}auth/verify-page/{user.verification_token}"
        
        msg = Message(
            subject='Verify your S-Chat account',
            recipients=[user.email],
            sender=current_app.config.get('MAIL_DEFAULT_SENDER') or mail_username,
            html=f'''
            <h2>Welcome to S-Chat!</h2>
            <p>Hello {user.username},</p>
            <p>Please verify your email by clicking the link below:</p>
            <a href="{verification_url}" style="
                display: inline-block; 
                padding: 12px 24px; 
                background: #007bff; 
                color: white; 
                text-decoration: none; 
                border-radius: 5px;
            ">Verify Email</a>
            <p>Or copy and paste this link in your browser:</p>
            <p><code>{verification_url}</code></p>
            <p>If you didn't create an account, please ignore this email.</p>
            '''
        )
        
        mail.send(msg)
        logging.info(f"✅ Verification email sent to {user.email}")
        return True
        
    except Exception as e:
        logging.error(f"❌ Failed to send verification email: {str(e)}")
        # При ошибке отправки переключаемся в режим разработки
        return send_verification_email_development(user)

def send_verification_email_development(user):
    """
    Режим разработки - выводит ссылку в консоль и автоматически верифицирует
    """
    try:
        verification_url = f"{request.host_url}auth/verify-page/{user.verification_token}"
        
        print("\n" + "="*60)
        print("🎯 DEVELOPMENT MODE: EMAIL VERIFICATION")
        print("="*60)
        print(f"📧 To: {user.email}")
        print(f"🔗 Verification URL: {verification_url}")
        print("="*60)
        print("💡 Since email is not configured, the account has been")
        print("   automatically verified for development purposes.")
        print("="*60 + "\n")
        
        # Автоматически верифицируем аккаунт для разработки
        user.email_verified = True
        user.verification_token = None
        db.session.commit()
        
        logging.info(f"🔄 Auto-verified user {user.email} for development")
        return False  # Возвращаем False, т.к. письмо не отправлялось
        
    except Exception as e:
        logging.error(f"❌ Development email failed: {str(e)}")
        return False

@auth_bp.route('/test-email-config', methods=['GET'])
def test_email_config():
    """
    Тестовый эндпоинт для проверки конфигурации email
    """
    config_info = {
        'MAIL_SERVER': current_app.config.get('MAIL_SERVER'),
        'MAIL_PORT': current_app.config.get('MAIL_PORT'),
        'MAIL_USERNAME': current_app.config.get('MAIL_USERNAME'),
        'MAIL_USE_TLS': current_app.config.get('MAIL_USE_TLS'),
        'MAIL_USE_SSL': current_app.config.get('MAIL_USE_SSL'),
        'MAIL_DEFAULT_SENDER': current_app.config.get('MAIL_DEFAULT_SENDER'),
        'has_mail_credentials': bool(current_app.config.get('MAIL_USERNAME') and current_app.config.get('MAIL_PASSWORD'))
    }
    
    return jsonify(config_info), 200