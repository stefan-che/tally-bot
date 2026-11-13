"""tx.message_id

Revision ID: fc7e4d8a06ba
Revises: 2bac21b5bb2c
Create Date: 2025-02-03 18:33:58.498967

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fc7e4d8a06ba'
down_revision = '2bac21b5bb2c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('history', sa.Column('message_id', sa.BigInteger(), nullable=True))


def downgrade() -> None:
    op.drop_column('history', 'message_id')
