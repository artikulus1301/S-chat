#!/usr/bin/env python3
"""
prepare_deploy.py — автоматическая подготовка Flask-проекта к деплою на Render.
Не трогает run.py, если он уже есть.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def backup_if_exists(path: Path):
    """Создаёт .bak резервную копию, если файл уже существует."""
    if path.exists():
        bak = path.with_suffix(path.suffix + ".bak")
        counter = 1
        while bak.exists():
            bak = path.with_suffix(path.suffix + f".bak{counter}")
            counter += 1
        shutil.copy2(path, bak)
        print(f"📦 Backup: {path} -> {bak}")


def write_file(path: Path, content: str):
    """Записывает файл, делая резервную копию, если нужно."""
    path.parent.mkdir(parents=True, exist_ok=True)
    backup_if_exists(path)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✍️  Written: {path}")


def generate_requirements():
    """Создаёт requirements.txt с актуальными зависимостями."""
    print("🔧 Генерация requirements.txt...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "freeze"],
            capture_output=True,
            text=True,
            check=True,
        )
        if not result.stdout.strip():
            print("⚠️ pip freeze ничего не вернул.")
        write_file(ROOT / "requirements.txt", result.stdout)
    except Exception as e:
        print(f"❌ Ошибка при генерации зависимостей: {e}")


def ensure_git():
    """Проверяет инициализацию git-репозитория."""
    if not (ROOT / ".git").exists():
        try:
            subprocess.run(["git", "init"], cwd=str(ROOT), check=True)
            print("✅ Git репозиторий инициализирован.")
        except Exception as e:
            print(f"⚠️ Не удалось инициализировать git: {e}")
    else:
        print("🟢 Git уже инициализирован.")


def create_render_yaml():
    """Создаёт render.yaml, если его нет."""
    path = ROOT / "render.yaml"
    if path.exists():
        print("🟡 render.yaml уже существует — пропускаем.")
        return

    content = """services:
  - type: web
    name: secure-chat
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python run.py"
    envVars:
      - key: FLASK_ENV
        value: production
      - key: BASE_URL
        value: "https://your-app.onrender.com"
"""
    write_file(path, content)


def create_gitignore():
    """Создаёт или дополняет .gitignore безопасными записями."""
    path = ROOT / ".gitignore"
    template = """# Python
__pycache__/
*.pyc
*.pyo
*.pyd

# Virtual environments
venv/
.env/
.venv/
env/

# Instance / local DB / uploads
instance/
*.db
*.sqlite3
uploads/
app/static/uploads/

# OS files
.DS_Store
Thumbs.db

# Secrets
.env
.env.local

# Tests / cache
.coverage
htmlcov/
build/
"""

    if path.exists():
        existing = path.read_text(encoding="utf-8")
        missing_lines = [
            line for line in template.splitlines() if line and line not in existing
        ]
        if missing_lines:
            with open(path, "a", encoding="utf-8") as f:
                f.write("\n# Added by prepare_deploy.py\n")
                f.write("\n".join(missing_lines))
            print("✅ .gitignore обновлён.")
        else:
            print("🟢 .gitignore уже содержит все нужные записи.")
    else:
        write_file(path, template)


def main():
    print("\n🚀 Подготовка проекта к деплою на Render...\n")

    # 1. Проверить наличие run.py
    if (ROOT / "run.py").exists():
        print("✅ run.py найден.")
    else:
        print("⚠️ run.py не найден! Render не сможет запустить приложение.")

    # 2. Создать/обновить файлы
    generate_requirements()
    create_render_yaml()
    create_gitignore()
    ensure_git()

    print("\n✅ Подготовка завершена.")
    print("\n🔹 Следующие шаги:")
    print("  1️⃣ Зайди на https://render.com и создай новый Web Service (Python).")
    print("  2️⃣ Подключи этот репозиторий (GitHub или GitLab).")
    print("  3️⃣ Добавь в настройках Render переменные окружения (.env):")
    print("      MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD, BASE_URL и т.д.")
    print("  4️⃣ После билда Render сам запустит python run.py 🚀\n")


if __name__ == "__main__":
    main()
