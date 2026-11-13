"""is_cannceled_null

Revision ID: aff118dbd938
Revises: 840e780867c6
Create Date: 2025-02-14 15:47:31.567689

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'aff118dbd938'
down_revision = '840e780867c6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # make is_canceled nullable in history table
    op.alter_column('history', 'is_cancelled', existing_type=sa.Boolean(), nullable=True)
    


def downgrade() -> None:
    # make is_canceled not nullable in history table
    op.alter_column('history', 'is_cancelled', existing_type=sa.Boolean(), nullable=False)
