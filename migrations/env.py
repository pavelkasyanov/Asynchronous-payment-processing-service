import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.database import Base

# this is the Alembic Config object
cfg = context.config

if cfg.config_file_name is not None:
    fileConfig(cfg.config_file_name)

# Set database URL from environment or default
db_url = cfg.get_main_option("sqlalchemy.url")
if not db_url:
    db_url = "postgresql+asyncpg://user:password@localhost:5432/payments"
cfg.set_main_option("sqlalchemy.url", db_url)


# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = cfg.get_main_option("my_important_option")
# my_other_value = cfg.cli.append()

# we call run_migrations_online which does all the heavy lifting
# run_migrations_online(metadata)


def run_migrations_offline() -> None:

    url = cfg.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    connectable = async_engine_from_config(
        cfg.get_section(cfg.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
