from sqlalchemy import Column, Integer, BigInteger, ForeignKey, Sequence, Float, UUID, UniqueConstraint, Index, VARCHAR
from sqlalchemy.orm import relationship
from uuid import uuid4
from .base import BaseModel

TABLE_ID = Sequence('table_id_seq', start=1)

class Account(BaseModel):
    __tablename__ = "accounts"

    id = Column(UUID(as_uuid=True), primary_key=True,
                unique=True, default=uuid4)

    # `group_id
    group_id = Column(ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    # `telegram chat_id where the accounts live
    user_id = Column(BigInteger, nullable=False)
    # `Account name
    name = Column(VARCHAR(32), nullable=False)
    # `Account name (used as the currency label)
    currency = Column(VARCHAR(32), nullable=False)
    # `Account balance
    amount = Column(Float, nullable=False, default=0)
    # `Number of decimal places
    decimal = Column(Integer, default=2)
    # `Relation to groups
    group = relationship("Group", back_populates="accounts", foreign_keys=[group_id])
    # `Relation to history
    histories = relationship("History", back_populates="account", primaryjoin="Account.id==History.account_id")
    # `Account wallets
    wallets = relationship("AccountWallet", back_populates="account", cascade="all, delete-orphan")

    # `Account names are unique per chat.
    __table_args__ = (
        UniqueConstraint(user_id, currency),
        Index("ix_accounts_group_id", "group_id"),
        Index("ix_accounts_user_id", "user_id"),
        {},
    )  # prettier-ignore

    def __str__(self) -> str:
        return f'ACCOUNT: {self.id} {self.currency} {self.amount}';

    def __repr__(self) -> str:
        return f'ACCOUNT: {self.id} {self.currency} {self.amount}';
