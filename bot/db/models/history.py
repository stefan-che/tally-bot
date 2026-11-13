import datetime
from sqlalchemy import Column, VARCHAR, BigInteger, Sequence, Float, DateTime, ForeignKey, UUID, Boolean
from sqlalchemy.orm import relationship
from .base import BaseModel
from uuid import uuid4

TABLE_ID = Sequence('table_id_seq', start=1)

class History(BaseModel):
    __tablename__ = "history"
    # * Operation history
    id = Column(UUID(as_uuid=True), primary_key=True,
                unique=True, default=uuid4)

    # `Telegram user id
    user_id = Column(ForeignKey("users.id"), nullable=True)
    # `account_id links to the account; set to NULL when the account is deleted`
    account_id = Column(ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    group_id = Column(ForeignKey("groups.id", ondelete="SET NULL"), nullable=True)
    # `Account name
    currency = Column(VARCHAR, nullable=False)
    # `Operation amount
    count = Column(Float, nullable=False)
    # `Operation comment
    comment = Column(VARCHAR, nullable=False)
    # `Operation date
    time = Column(DateTime, default=datetime.datetime.utcnow)
    # `User name
    username = Column(VARCHAR)
    #
    is_cancelled = Column(Boolean, default=False, nullable=True)

    # `ID of the message linked to the operation
    message_id = Column(BigInteger, nullable=True)

    user = relationship("User", back_populates="histories", foreign_keys=[user_id])
    account = relationship("Account", back_populates="histories", foreign_keys=[account_id])
    group = relationship("Group", back_populates="histories", foreign_keys=[group_id])
    
    
    def __str__(self) -> str:
        return f'History: {self.currency} {self.count} "{self.group_id}" by "{self.username or self.user_id}" ';
