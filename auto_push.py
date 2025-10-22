import subprocess
import sys
from datetime import datetime

def run(cmd):
    """Запуск команды и вывод в консоль"""
    print(f"🚀 {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"❌ Ошибка при выполнении: {cmd}")
        sys.exit(result.returncode)

def main():
    # Формируем сообщение коммита с текущей датой
    commit_message = f"Auto commit — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    print("🔍 Проверяем статус репозитория...")
    run("git status")

    print("📦 Добавляем все изменения...")
    run("git add .")

    print(f"📝 Создаём коммит: {commit_message}")
    run(f'git commit -m "{commit_message}" || echo "⚠️ Нет изменений для коммита"')

    print("🌐 Отправляем на GitHub...")
    run("git push origin main || git push origin master")

    print("✅ Готово! Изменения успешно отправлены 🚀")

if __name__ == "__main__":
    main()
