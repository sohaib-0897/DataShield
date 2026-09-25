"""Database connection shared by the API and development utilities."""
import os
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv(Path(__file__).resolve().parents[2] / '.env')


class Base(DeclarativeBase):
    pass


def database_url():
    url = os.getenv('DATABASE_URL')
    if not url:
        raise RuntimeError('DATABASE_URL must be set in .env')
    return url


engine = create_engine(database_url(), pool_pre_ping=True)
Session = sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def session_scope():
    with Session.begin() as session:
        yield session
