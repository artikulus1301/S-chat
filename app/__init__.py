from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_mail import Mail
from flask_migrate import Migrate
from flask_cors import CORS
import os
from dotenv import load_dotenv
from config import Config
import requests  # 👈 понадобится для скачивания socket.io.min.js

# --- Загрузить .env до создания приложения ---
load_dotenv()

db = SQLAlchemy()
socketio = SocketIO()
mail = Mail()
migrate = Migrate()


def ensure_static_files():
    """Проверяет и создает недостающие статические файлы."""
    static_js = os.path.join('app', 'static', 'js')
    os.makedirs(static_js, exist_ok=True)

    # Проверяем наличие socket.io.min.js
    socketio_js = os.path.join(static_js, 'socket.io.min.js')
    if not os.path.exists(socketio_js):
        print("⚙️  Downloading socket.io.min.js...")
        url = "https://cdn.socket.io/4.7.5/socket.io.min.js"
        try:
            r = requests.get(url)
            r.raise_for_status()
            with open(socketio_js, "wb") as f:
                f.write(r.content)
            print("✅ socket.io.min.js saved to /static/js/")
        except Exception as e:
            print(f"❌ Failed to download socket.io.min.js: {e}")

    # Создаем favicon, если отсутствует
    static_dir = os.path.join('app', 'static')
    favicon_path = os.path.join(static_dir, 'favicon.ico')
    if not os.path.exists(favicon_path):
        print("⚙️  Creating placeholder favicon.ico...")
        try:
            with open(favicon_path, "wb") as f:
                # Минимальный пустой favicon (валидный 16×16 ICO)
                f.write(b'\x00\x00\x01\x00\x01\x00\x10\x10\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00')
            print("✅ favicon.ico created")
        except Exception as e:
            print(f"❌ Failed to create favicon: {e}")


def create_app(config_class=Config):
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')

    # Применить конфигурацию
    app.config.from_object(config_class)

    # Убедиться, что нужные папки существуют
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['SIGNAL_PROTOCOL_STORE'], exist_ok=True)

    # Инициализация расширений
    db.init_app(app)
    socketio.init_app(
        app,
        cors_allowed_origins="*",
        async_mode='threading',
        logger=True,
        engineio_logger=True
    )
    mail.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    # Регистрация blueprints
    from app.routes.auth import auth_bp
    from app.routes.chats import chats_bp
    from app.routes.uploads import uploads_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(chats_bp, url_prefix='/chats')
    app.register_blueprint(uploads_bp, url_prefix='/uploads')

    # Главная страница
    @app.route('/')
    def index():
        return render_template('index.html')

    # Заглушка для favicon, чтобы не было 404
    @app.route('/favicon.ico')
    def favicon():
        return '', 204

    # Проверка статических файлов
    ensure_static_files()

    # Импорт и регистрация socket.io событий
    from app.sockets import connection, events
    socketio.on_namespace(connection.ChatNamespace('/chat'))

    # Проверка конфигурации почты
    print(f"📧 MAIL_USERNAME: {app.config.get('MAIL_USERNAME')}")

    return app
