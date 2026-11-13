from sqlalchemy import Column, VARCHAR,  UUID, ForeignKey
from sqlalchemy.orm import relationship
from uuid import uuid4
from .base import BaseModel
from .user import EUserRole

class Assigner(BaseModel):
    __tablename__ = "assigners"

    id = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid4)
    # `Telegram user id`
    user_id = Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    # `Group id; the assigner is deleted with the group`
    group_id = Column(ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)

    # `User role in the group`
    role = Column(VARCHAR(32), nullable=False, default=EUserRole.USER)

    # `Relation to users`
    user = relationship("User", back_populates="assigners", foreign_keys=[user_id])
    # `Relation to groups`
    group = relationship("Group", back_populates="assigners", foreign_keys=[group_id])