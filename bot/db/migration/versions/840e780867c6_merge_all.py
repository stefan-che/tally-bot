"""merge_all

Revision ID: 840e780867c6
Revises: 2bac21b5bb2c, fc7e4d8a06ba
Create Date: 2025-02-13 16:15:39.674650

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '840e780867c6'
down_revision = ('2bac21b5bb2c', 'fc7e4d8a06ba')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
