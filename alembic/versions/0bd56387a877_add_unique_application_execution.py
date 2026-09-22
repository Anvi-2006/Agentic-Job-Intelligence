"""add unique application execution

Revision ID: 0bd56387a877
Revises: 372cc8e18b19
Create Date: 2026-09-19

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "0bd56387a877"
down_revision: Union[str, Sequence[str], None] = "372cc8e18b19"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint(
        "uq_application_executions_application_id",
        "application_executions",
        ["application_id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "uq_application_executions_application_id",
        "application_executions",
        type_="unique",
    )
