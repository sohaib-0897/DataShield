"""Configuration, database sessions and authentication primitives."""
import os
from datetime import datetime, timedelta, timezone
from functools import lru_cache

import jwt
from dotenv import load_dotenv
from pwdlib import PasswordHash
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()


class Base(DeclarativeBase):
    pass


@lru_cache
def settings():
    return {
        "database_url": os.getenv("DATABASE_URL", "postgresql+psycopg://datashield:datashield@localhost:5432/datashield"),
        "jwt_secret": os.getenv("DATASHIELD_JWT_SECRET", ""),
        "agent_key": os.getenv("DATASHIELD_AGENT_KEY", ""),
        "origin": os.getenv("DATASHIELD_FRONTEND_ORIGIN", "http://localhost:3000"),
    }


def require_secrets():
    for name in ("jwt_secret", "agent_key"):
        if len(settings()[name]) < 32 or settings()[name].startswith("replace-with-"):
            raise RuntimeError(f"Configure a random 32-character or longer {name} before starting DataShield")


engine = create_engine(settings()["database_url"], pool_pre_ping=True)
SessionLocal = sessionmaker(engine, expire_on_commit=False)
password_hash = PasswordHash.recommended()


def now():
    return datetime.now(timezone.utc)


def token_for(user):
    require_secrets()
    return jwt.encode({"sub": str(user.id), "exp": now() + timedelta(hours=8)}, settings()["jwt_secret"], algorithm="HS256")
