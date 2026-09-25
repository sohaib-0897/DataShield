from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from database import Base, database_url
import models  # noqa: F401 - registers model metadata
from app import models as datashield_models  # noqa: F401
from app.core import Base as NewBase

config = context.config
config.set_main_option('sqlalchemy.url', database_url().replace('%', '%%'))
if config.config_file_name:
    fileConfig(config.config_file_name)
target_metadata = [Base.metadata, NewBase.metadata]


def run_migrations_offline():
    context.configure(url=database_url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    engine = engine_from_config(config.get_section(config.config_ini_section),
                                prefix='sqlalchemy.', poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
