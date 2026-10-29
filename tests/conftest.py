"""
Pytest configuration and fixtures for MediApp test suites.
Creates isolated test database, populates seed data, and provides authenticated test clients.
"""
import os
import tempfile
import pytest
from app import create_app
from app.config import TestingConfig
from app.database import init_db
from app.seed import seed_database

@pytest.fixture(scope="session")
def app():
    """Creates test application instance with temporary database."""
    db_fd, db_path = tempfile.mkstemp(suffix="_test_mediapp.db")
    os.close(db_fd)

    class CustomTestingConfig(TestingConfig):
        DATABASE_PATH = db_path
        TESTING = True
        WTF_CSRF_ENABLED = False

    app = create_app(CustomTestingConfig)
    
    with app.app_context():
        init_db(db_path)
        seed_database(db_path)

    yield app

    # Cleanup temp database
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass

@pytest.fixture
def client(app):
    """Test client with session cookie persistence."""
    return app.test_client()

@pytest.fixture
def auth_client(client):
    """Factory fixture returning an authenticated client for specified role."""
    def _auth(role="customer"):
        res = client.post("/api/auth/demo-login", json={"role": role})
        assert res.status_code == 200, f"Failed demo login for role {role}"
        return client
    return _auth
