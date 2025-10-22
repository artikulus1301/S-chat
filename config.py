import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    # --- Flask core settings ---
    SECRET_KEY = os.getenv("SECRET_KEY", os.urandom(24))
    DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

    # --- Database ---
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(basedir, 'app.db')}"  # дефолт — SQLite
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Mail settings ---
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True").lower() in ("true", "1", "yes")
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "False").lower() in ("true", "1", "yes")
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", MAIL_USERNAME)

    # --- Application URLs ---
    BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")

    # --- Upload folders ---
    UPLOAD_FOLDER = os.path.join(basedir, "app", "static", "uploads")
    SIGNAL_PROTOCOL_STORE = os.path.join(basedir, "app", "encryption", "signal_store")

    # --- Security / Auth ---
    SECURITY_PASSWORD_SALT = os.getenv("SECURITY_PASSWORD_SALT", "default_salt")

    # --- SocketIO ---
    SOCKET_IO_MESSAGE_QUEUE = os.getenv("SOCKET_IO_MESSAGE_QUEUE", None)
