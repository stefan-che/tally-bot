"""account_wallet_and_indexes

Revision ID: a1b2c3d4e5f6
Revises: 840e780867c6
Create Date: 2026-05-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'a1b2c3d4e5f6'
down_revision = 'aff118dbd938'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('accounts', sa.Column('wallet_address', sa.VARCHAR(64), nullable=True))
    op.create_index('ix_accounts_group_id', 'accounts', ['group_id'])
    op.create_index('ix_accounts_user_id', 'accounts', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_accounts_user_id', table_name='accounts')
    op.drop_index('ix_accounts_group_id', table_name='accounts')
    op.drop_column('accounts', 'wallet_address')