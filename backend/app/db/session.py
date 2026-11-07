import logging
from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# Normalize postgresql database URL for SQLAlchemy
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
# SQLAlchemy 2.1 maps a bare "postgresql://" to psycopg (v3); this project ships psycopg2-binary.
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

connect_args = {}
if "sqlite" in db_url:
    connect_args["check_same_thread"] = False
    connect_args["timeout"] = 30

engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True
)

if "sqlite" in db_url:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Bring the database schema up to date with Alembic migrations.

    `create_all` only creates missing tables and silently ignores new columns, which breaks
    existing databases when the models change. Migrations evolve the schema safely on SQLite
    and PostgreSQL alike. Databases created before migrations existed are detected and adopted.
    """
    import os
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import inspect

    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cfg = Config(os.path.join(backend_dir, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(backend_dir, "alembic"))
    cfg.attributes["configure_logger"] = False

    with engine.begin() as connection:
        cfg.attributes["connection"] = connection
        insp = inspect(connection)
        tables = set(insp.get_table_names())
        if tables and "alembic_version" not in tables and "accounts" in tables:
            # Legacy database created with create_all: adopt it at the matching revision.
            cols = {c["name"] for c in insp.get_columns("accounts")}
            command.stamp(cfg, "0002" if "fraud_role" in cols else "0001")
        command.upgrade(cfg, "head")
