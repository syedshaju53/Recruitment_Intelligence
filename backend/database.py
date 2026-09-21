import os

import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()


def get_database_url():
    """
    Get the database URL from Streamlit Cloud Secrets first,
    then fall back to the local .env environment.
    """

    try:
        database_url = st.secrets.get("DATABASE_URL")
    except Exception:
        database_url = None

    if not database_url:
        database_url = os.getenv("DATABASE_URL")

    if not database_url:
        # Build the URL from PostgreSQL connection variables.
        try:
            db_host = st.secrets.get("POSTGRES_HOST")
            db_port = st.secrets.get("POSTGRES_PORT", "5432")
            db_name = st.secrets.get("POSTGRES_DB")
            db_user = st.secrets.get("POSTGRES_USER")
            db_password = st.secrets.get("POSTGRES_PASSWORD")
        except Exception:
            db_host = None
            db_port = "5432"
            db_name = None
            db_user = None
            db_password = None

        db_host = db_host or os.getenv("POSTGRES_HOST")
        db_port = db_port or os.getenv("POSTGRES_PORT", "5432")
        db_name = db_name or os.getenv("POSTGRES_DB")
        db_user = db_user or os.getenv("POSTGRES_USER")
        db_password = db_password or os.getenv("POSTGRES_PASSWORD")

        if all([db_host, db_port, db_name, db_user, db_password]):
            from urllib.parse import quote_plus

            database_url = (
                f"postgresql+psycopg2://"
                f"{quote_plus(db_user)}:"
                f"{quote_plus(db_password)}@"
                f"{db_host}:{db_port}/"
                f"{db_name}"
            )

    if not database_url:
        raise ValueError("DATABASE_URL is not configured")


    return database_url


DATABASE_URL = get_database_url()

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=1800,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()