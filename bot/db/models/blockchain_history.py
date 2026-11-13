import datetime
from sqlalchemy import Column, VARCHAR, Float, DateTime, ForeignKey, UUID, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from uuid import uuid4
from .base import BaseModel


class BlockchainHistory(BaseModel):
    __tablename__ = "blockchain_history"

    id = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid4)
    account_id = Column(ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    group_id = Column(ForeignKey("groups.id", ondelete="SET NULL"), nullable=True)
    wallet_id = Column(ForeignKey("accounts_wallets.id", ondelete="SET NULL"), nullable=True)
    wallet_address = Column(VARCHAR(64), nullable=True)

    currency = Column(VARCHAR, nullable=False)
    count = Column(Float, nullable=False)
    comment = Column(VARCHAR, nullable=False)
    time = Column(DateTime, default=datetime.datetime.utcnow)
    txid = Column(VARCHAR(128), nullable=False)

    __table_args__ = (
        UniqueConstraint("wallet_id", "txid", name="uq_blockchain_history_wallet_txid"),
        Index("ix_blockchain_history_account_id", "account_id"),
        Index("ix_blockchain_history_wallet_id", "wallet_id"),
    )

    account = relationship("Account", foreign_keys=[account_id])
    group = relationship("Group", foreign_keys=[group_id])
    wallet = relationship("AccountWallet", foreign_keys=[wallet_id])

    def __str__(self):
        return f"BlockchainHistory: {self.txid} {self.currency} {self.count}"
