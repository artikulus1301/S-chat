import os
import subprocess
from textwrap import dedent

print("🚄 Preparing project for Railway deployment...\n")

# --- 1. Проверка основных директорий ---
required_dirs = ["app", "app/routes", "app/templates", "app/static"]
for d in required_dirs:
    os.makedirs(d, exist_ok=True)
    print(f"✅ Ensured directory: {d}")

# --- 2. Procfile ---
procfile_content = "web: gunicorn run:app --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker --bind 0.0.0.0:$PORT\n"
with open("Procfile", "w", encoding="utf-8") as f:
    f.write(procfile_content)
print("✅ Created Procfile")

# --- 3. runtime.txt (указывает Railway на Python-версию) ---
with open("runtime.txt", "w", encoding="utf-8") as f:
    f.write("python-3.12.6\n")
print("✅ Created runtime.txt")

# --- 4. requirements.txt ---
requirements = dedent("""\
    Flask
    Flask-SocketIO
    Flask-Mail
    Flask-Migrate
    Flask-Cors
    Flask-SQLAlchemy
    python-dotenv
    gunicorn
    gevent
    gevent-websocket
    requests
""")

with open("requirements.txt", "w", encoding="utf-8") as f:
    f.write(requirements)
print("✅ Created/updated requirements.txt")

# --- 5. .env.example (без приватных данных) ---
env_example = dedent("""\
    MAIL_SERVER=smtp.gmail.com
    MAIL_PORT=587
    MAIL_USE_TLS=True
    MAIL_USERNAME=youremail@gmail.com
    MAIL_PASSWORD=your_app_password
    MAIL_DEFAULT_SENDER=youremail@gmail.com
    DATABASE_URL=sqlite:///site.db
    SECRET_KEY=supersecretkey
""")

with open(".env.example", "w", encoding="utf-8") as f:
    f.write(env_example)
print("✅ Created .env.example")

# --- 6. .gitignore ---
gitignore = dedent("""\
    __pycache__/
    *.pyc
    *.pyo
    *.pyd
    *.db
    *.sqlite3
    .env
    venv/
    .venv/
    instance/
    .DS_Store
""")

with open(".gitignore", "w", encoding="utf-8") as f:
    f.write(gitignore)
print("✅ Created .gitignore")

# --- 7. Проверка run.py ---
if not os.path.exists("run.py"):
    with open("run.py", "w", encoding="utf-8") as f:
        f.write(dedent("""\
            from app import create_app, socketio

            app = create_app()

            if __name__ == "__main__":
                socketio.run(app, host="0.0.0.0", port=5000, debug=True)
        """))
    print("✅ Created run.py (default Flask entry point)")
else:
    print("ℹ️ run.py already exists, leaving it unchanged.")

# --- 8. Проверка GIT ---
if not os.path.exists(".git"):
    print("\n🧩 Initializing git repository...")
    subprocess.run(["git", "init"])
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", "Prepare project for Railway deployment"])
    print("✅ Git initialized and first commit created.")
else:
    print("✅ Git repo already exists.")

print("\n🎉 Project is ready for Railway deployment!")
print("👉 Next steps:")
print("   1. Push project to GitHub: git add . && git commit -m 'Ready for Railway' && git push")
print("   2. Go to https://railway.app → New Project → Deploy from GitHub")
print("   3. Add variables from .env.example to Railway Variables panel")
print("   4. Deploy 🚀")
