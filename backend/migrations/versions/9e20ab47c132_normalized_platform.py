"""Normalized DataShield platform tables, preserving legacy records.

Revision ID: 9e20ab47c132
Revises: 5b28af0081a1
"""
from alembic import op
from app.core import Base
from app import models  # noqa: F401

revision = "9e20ab47c132"
down_revision = "5b28af0081a1"
branch_labels = None
depends_on = None


def upgrade():
    # Metadata is the single source of truth for the new, separately named tables.
    Base.metadata.create_all(bind=op.get_bind())


def downgrade():
    Base.metadata.drop_all(bind=op.get_bind())
