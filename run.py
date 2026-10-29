"""
MediApp Entrypoint Script.
Initializes the application, validates configuration, and starts the development server.
"""
from app import create_app
from app.config import Config
from app.migrations import apply_migrations
from app.seed import seed_database

# Apply schema migrations and idempotent initial seeding
apply_migrations()
seed_database()

app = create_app()

if __name__ == "__main__":
    print(f"==================================================")
    print(f" MediApp Starting")
    print(f" Environment : {Config.APP_ENV}")
    print(f" Mode        : {Config.APP_MODE.upper()}")
    print(f" Database    : {Config.DATABASE_PATH}")
    print(f" Listening on: http://{Config.HOST}:{Config.PORT}")
    print(f"==================================================")
    app.run(host=Config.HOST, port=Config.PORT, debug=True)
