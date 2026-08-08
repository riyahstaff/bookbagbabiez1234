from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401 - ensures all models are registered on Base.metadata
from app.database import Base, get_db
from app.main import app
from app.storage import get_storage
from app.storage.local import LocalStorageBackend


@pytest.fixture()
def db_session() -> Generator:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = testing_session_local()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def test_storage(tmp_path) -> LocalStorageBackend:
    return LocalStorageBackend(tmp_path / "series")


@pytest.fixture()
def client(db_session, test_storage) -> Generator:
    def _override_get_db() -> Generator:
        yield db_session

    def _override_get_storage() -> LocalStorageBackend:
        return test_storage

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_storage] = _override_get_storage
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
