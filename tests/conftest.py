"""
Pytest configuration and shared fixtures.

Uses an in-memory SQLite database so no real PostgreSQL instance is required.
The DATABASE_URL environment variable is set before any app modules are imported.
"""
import os
import pytest

# Must be set BEFORE any app module is imported so database.py uses SQLite.
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.models.models import Base
from app.database import get_db
from app.main import app

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_database():
    """Create all tables before each test and drop them after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session():
    """Provide a transactional database session for a test."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client():
    """FastAPI TestClient with the database dependency overridden."""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, base_url="http://testserver") as c:
        yield c
    app.dependency_overrides.clear()
