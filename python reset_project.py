import os
import shutil
from app import create_app, db

def safe_rmdir(path):
    """Удаляет директорию, если существует"""
    if os.path.exists(path):
        shutil.rmtree(path, ignore_errors=True)
        print(f"🗑️  Удалена папка: {path}")

def safe_remove(path):
    """Удаляет файл, если существует"""
    if os.path.exists(path):
        os.remove(path)
        print(f"🗑️  Удалён файл: {path}")

def recreate_db():
    """Пересоздаёт базу данных"""
    app = create_app()
    with app.app_context():
        db.create_all()
        print("✅ Новая база данных успешно создана.")

def main():
    print("🧭 Secure-Chat Reset Utility\n")

    # 1. Удаляем базу данных
    safe_remove("s-chat.db")
    safe_remove("instance/s-chat.db")

    # 2. Удаляем миграции
    safe_rmdir("migrations")

    # 3. Удаляем ключи Signal Protocol
    safe_rmdir("instance/keys")

    # 4. Очищаем загрузки
    safe_rmdir("app/static/uploads")
    os.makedirs("app/static/uploads", exist_ok=True)

    # 5. Удаляем __pycache__
    for root, dirs, files in os.walk("app"):
        for d in dirs:
            if d == "__pycache__":
                cache_dir = os.path.join(root, d)
                safe_rmdir(cache_dir)

    # 6. Пересоздаём базу
    recreate_db()

    print("\n🎉 Полный сброс проекта выполнен успешно!")
    print("➡️  Теперь можешь заново зарегистрировать первого пользователя.")

if __name__ == "__main__":
    main()
