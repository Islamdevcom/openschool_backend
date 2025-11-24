from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, create_engine
from alembic import context
import os
import sys

# === Добавляем путь до корня проекта ===
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# === Импортируем app так же, как в main.py ===
from app.database import Base
from app import models  # все модели регистрируются здесь

# Конфигурация Alembic
config = context.config

# Получаем DATABASE_URL из переменной окружения или используем SQLite
database_url = os.getenv("DATABASE_URL", "sqlite:///./test.db")
config.set_main_option("sqlalchemy.url", database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    url = config.get_main_option("sqlalchemy.url")

    # Создаём engine напрямую вместо использования config
    connectable = create_engine(url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
