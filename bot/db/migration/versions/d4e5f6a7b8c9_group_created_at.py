"""group created_at

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-11-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # No server_default at first: otherwise Postgres fills old rows with the current now()
    op.add_column('groups', sa.Column('created_at', sa.DateTime(), nullable=True))
    # Old groups: date of the first operation; no operations — NULL (no made-up dates)
    op.execute(
        "UPDATE groups SET created_at = "
        "(SELECT min(h.time) FROM history h WHERE h.group_id = groups.id)"
    )
    op.alter_column('groups', 'created_at', server_default=sa.text('now()'))


def downgrade() -> None:
    op.drop_column('groups', 'created_at')
