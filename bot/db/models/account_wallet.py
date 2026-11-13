from sqlalchemy import Column, VARCHAR, Float, ForeignKey, UUID, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from uuid import uuid4
from .base import BaseModel


class AccountWallet(BaseModel):
    __tablename__ = "accounts_wallets"

    id = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid4)
    account_id = Column(ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    wallet_address = Column(VARCHAR(64), nullable=False)
    network = Column(VARCHAR(32), nullable=False, default="tron")
    balance = Column(Float, nullable=False, default=0)

    account = relationship("Account", back_populates="wallets")

    __table_args__ = (
        UniqueConstraint("account_id", "wallet_address", name="uq_accounts_wallets"),
        Index("ix_accounts_wallets_account_id", "account_id"),
        Index("ix_accounts_wallets_address", "wallet_address"),
    )

    def __repr__(self):
        return f"AccountWallet({self.account_id}, {self.wallet_address})"
