import tempfile
import pytest
from app import create_app
from app.models import db
from app.config import Config


class TestConfig(Config):
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    UPLOAD_FOLDER = tempfile.mkdtemp(prefix="test_upload_")


@pytest.fixture(scope="session")
def app():
    test_app = create_app(TestConfig)

    with test_app.app_context():
        db.create_all()
        yield test_app


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()
