from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0cd9f2c98964"
down_revision: Union[str, Sequence[str], None] = "084f81ffea96"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns as nullable first so existing rows remain valid.
    op.add_column(
        "job_requirements",
        sa.Column(
            "normalized_name",
            sa.String(length=255),
            nullable=True,
        ),
    )

    op.add_column(
        "job_requirements",
        sa.Column(
            "original_text",
            sa.Text(),
            nullable=True,
        ),
    )

    op.add_column(
        "job_requirements",
        sa.Column(
            "context",
            sa.Text(),
            nullable=True,
        ),
    )

    op.add_column(
        "job_requirements",
        sa.Column(
            "category",
            sa.String(length=100),
            nullable=True,
        ),
    )

    op.add_column(
        "job_requirements",
        sa.Column(
            "confidence",
            sa.Float(),
            nullable=True,
        ),
    )

    op.add_column(
        "job_requirements",
        sa.Column(
            "source",
            sa.String(length=50),
            nullable=True,
        ),
    )

    # Backfill existing requirements.
    op.execute(
        """
        UPDATE job_requirements
        SET
            normalized_name = LOWER(TRIM(requirement)),
            original_text = requirement,
            context = requirement,
            category = CASE
                WHEN LOWER(requirement) IN (
                    'communication',
                    'teamwork',
                    'leadership',
                    'problem solving',
                    'cross-functional collaboration',
                    'technical writing'
                )
                THEN 'behavioral'
                ELSE 'technical'
            END,
            confidence = 1.0,
            source = 'migration'
        WHERE normalized_name IS NULL
        """
    )

    # These columns are now populated for existing records.
    op.alter_column(
        "job_requirements",
        "normalized_name",
        existing_type=sa.String(length=255),
        nullable=False,
    )

    op.alter_column(
        "job_requirements",
        "category",
        existing_type=sa.String(length=100),
        nullable=False,
    )

    op.alter_column(
        "job_requirements",
        "confidence",
        existing_type=sa.Float(),
        nullable=False,
    )

    op.alter_column(
        "job_requirements",
        "source",
        existing_type=sa.String(length=50),
        nullable=False,
    )

    # Replace the old uniqueness rule.
    op.drop_constraint(
        "uq_job_requirement_job_requirement",
        "job_requirements",
        type_="unique",
    )

    op.create_unique_constraint(
        "uq_job_requirement_job_normalized_name",
        "job_requirements",
        ["job_id", "normalized_name"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_job_requirement_job_normalized_name",
        "job_requirements",
        type_="unique",
    )

    op.create_unique_constraint(
        "uq_job_requirement_job_requirement",
        "job_requirements",
        ["job_id", "requirement"],
    )

    op.drop_column("job_requirements", "source")
    op.drop_column("job_requirements", "confidence")
    op.drop_column("job_requirements", "category")
    op.drop_column("job_requirements", "context")
    op.drop_column("job_requirements", "original_text")
    op.drop_column("job_requirements", "normalized_name")