from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from backend.app.core.database import Base
from backend.app.core.config import settings

# Import all models so SQLAlchemy registers them with Base.metadata
from backend.app.models.application import Application
from backend.app.models.candidate import CandidateProfile
from backend.app.models.candidate_evidence import CandidateEvidence
from backend.app.models.education import Education
from backend.app.models.job import Job
from backend.app.models.job_requirement import JobRequirement
from backend.app.models.project import Project
from backend.app.models.resume import Resume
from backend.app.models.skill import Skill
from backend.app.models.user import User


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in offline mode."""

    url = settings.database_url

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in online mode."""

    configuration = config.get_section(
        config.config_ini_section,
        {},
    )

    configuration["sqlalchemy.url"] = settings.database_url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()