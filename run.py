from app import create_app, socketio
from config import Config

app = create_app(Config)

# ДОБАВЬТЕ ЭТО ДЛЯ ДИАГНОСТИКИ
with app.app_context():
    print("=== AVAILABLE ENDPOINTS ===")
    for rule in app.url_map.iter_rules():
        if 'auth' in str(rule):
            print(f"{rule.endpoint}: {rule.rule} [{', '.join(rule.methods)}]")
    print("===========================")

if __name__ == '__main__':
    print("=== S-Chat Server ===")
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=False
    )