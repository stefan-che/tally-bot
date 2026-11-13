"""accounts_wallets and blockchain_history

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-30 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'accounts_wallets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('accounts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('wallet_address', sa.VARCHAR(64), nullable=False),
        sa.Column('balance', sa.Float(), nullable=False, server_default='0'),
        sa.UniqueConstraint('account_id', 'wallet_address', name='uq_accounts_wallets'),
    )
    op.create_index('ix_accounts_wallets_account_id', 'accounts_wallets', ['account_id'])
    op.create_index('ix_accounts_wallets_address', 'accounts_wallets', ['wallet_address'])

    # Move existing wallet_address values from accounts to accounts_wallets
    op.execute("""
        INSERT INTO accounts_wallets (id, account_id, wallet_address)
        SELECT gen_random_uuid(), id, wallet_address
        FROM accounts
        WHERE wallet_address IS NOT NULL
    """)

    # Blockchain history table (for wallet_sync; manual operations stay in history)
    op.create_table(
        'blockchain_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('group_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('groups.id', ondelete='SET NULL'), nullable=True),
        sa.Column('wallet_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('accounts_wallets.id', ondelete='SET NULL'), nullable=True),
        sa.Column('wallet_address', sa.VARCHAR(64), nullable=True),
        sa.Column('currency', sa.VARCHAR(), nullable=False),
        sa.Column('count', sa.Float(), nullable=False),
        sa.Column('comment', sa.VARCHAR(), nullable=False),
        sa.Column('time', sa.DateTime(), nullable=True),
        sa.Column('txid', sa.VARCHAR(128), nullable=False),
        sa.UniqueConstraint('wallet_id', 'txid', name='uq_blockchain_history_wallet_txid'),
    )
    op.create_index('ix_blockchain_history_account_id', 'blockchain_history', ['account_id'])
    op.create_index('ix_blockchain_history_wallet_id', 'blockchain_history', ['wallet_id'])

    # Drop wallet_address from accounts (moved to accounts_wallets)
    op.drop_column('accounts', 'wallet_address')


def downgrade() -> None:
    op.add_column('accounts', sa.Column('wallet_address', sa.VARCHAR(64), nullable=True))

    # Restore wallet_address from the first wallet of each account
    op.execute("""
        UPDATE accounts a
        SET wallet_address = (
            SELECT wallet_address FROM accounts_wallets
            WHERE account_id = a.id
            ORDER BY wallet_address
            LIMIT 1
        )
    """)

    op.drop_index('ix_blockchain_history_wallet_id', table_name='blockchain_history')
    op.drop_index('ix_blockchain_history_account_id', table_name='blockchain_history')
    op.drop_table('blockchain_history')

    op.drop_index('ix_accounts_wallets_address', table_name='accounts_wallets')
    op.drop_index('ix_accounts_wallets_account_id', table_name='accounts_wallets')
    op.drop_table('accounts_wallets')
