from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel
# from myapp.database import engine  # Import your engine from FastAPI app

from alembic import context  # Import context from Alembic
config = context.config  # Define config from Alembic context

# Use SQLModel's metadata to generate migrations
target_metadata = SQLModel.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    from alembic import context
    context.configure(url="postgresql://myuser:mypassword@localhost:5432/mydatabase", target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    from alembic import context
    connectable = engine_from_config(config.get_section(config.config_ini_section), prefix="sqlalchemy.")

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()
