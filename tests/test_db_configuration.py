from sqlalchemy import create_engine, inspect

from app.core.config import Settings
from app.db.base import Base as ImportedBase
from app.db.base import KguContact as ImportedKguContact
from app.db.base import KguPlace as ImportedKguPlace
from app.db.session import get_connect_args
from app.models import Base, KguContact, KguPlace


def test_settings_uses_local_sqlite_database_by_default():
    settings = Settings(google_api_key="test-key", _env_file=None)

    assert settings.database_url == "sqlite:///./app.db"


def test_get_connect_args_allows_sqlite_thread_sharing_only_for_sqlite():
    assert get_connect_args("sqlite:///./app.db") == {"check_same_thread": False}
    assert get_connect_args("sqlite+pysqlite:///:memory:") == {"check_same_thread": False}
    assert get_connect_args("postgresql+psycopg2://user:pass@localhost:5432/app") == {}


def test_db_base_re_exports_metadata_and_models():
    assert ImportedBase is Base
    assert ImportedKguPlace is KguPlace
    assert ImportedKguContact is KguContact


def test_place_and_contact_names_are_unique_and_indexed():
    assert KguPlace.__table__.c.name.unique is True
    assert KguPlace.__table__.c.name.index is True
    assert KguContact.__table__.c.name.unique is True
    assert KguContact.__table__.c.name.index is True


def test_model_metadata_creates_expected_tables_and_indexes():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)

    assert set(inspector.get_table_names()) >= {"kgu_places", "kgu_contacts"}
    place_indexes = inspector.get_indexes("kgu_places")
    contact_indexes = inspector.get_indexes("kgu_contacts")

    assert any(index["column_names"] == ["name"] for index in place_indexes)
    assert any(index["column_names"] == ["name"] for index in contact_indexes)
