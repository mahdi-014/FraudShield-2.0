import os
import re
from logging.config import fileConfig
from fraudshield.db.session import get_engine
from alembic import context
from fraudshield.db.models import Base
from fraudshield.config import get_database_url

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = get_database_url() or config.get_main_option("sqlalchemy.url")
    if not url:
        raise RuntimeError('Set DATABASE_URL for offline migration generation')
    schema = os.environ.get('FRAUDSHIELD_DB_SCHEMA', 'public')
    if not re.fullmatch(r'[a-z_][a-z0-9_]{0,62}', schema):
        raise ValueError('Invalid database schema identifier')
    context.configure(
        url=url,
        version_table_schema=schema,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    context.execute(f'SET search_path TO "{schema}"')
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    url = get_database_url() or config.get_main_option("sqlalchemy.url")
    if not url:
        raise RuntimeError("DATABASE_URL is not set for Alembic migrations.")

    connectable = get_engine(url)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=os.environ.get('FRAUDSHIELD_DB_SCHEMA', 'public'),
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
