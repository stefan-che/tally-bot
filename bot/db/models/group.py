import datetime
from enum import Enum
from colorama import Fore
from aiogram.types import Message
from sqlalchemy import Column, VARCHAR, Integer, BigInteger, PrimaryKeyConstraint, Sequence, Float, UUID, UniqueConstraint, DateTime, func
from sqlalchemy.orm import relationship
from uuid import uuid4
from .base import BaseModel

class EGroupStatus(str, Enum):
    ACTIVE = 'Active'
    INACTIVE = 'Inactive'
    NEW = 'New'
    
    @staticmethod
    def get_emoji(status: str):
        if status == EGroupStatus.ACTIVE:
            return '🟩'
        elif status == EGroupStatus.INACTIVE:
            return '🟥'
        elif status == EGroupStatus.NEW:
            return '🟪'
        else:
            return '🔳'

class EGroupType(str, Enum):
    GROUP = 'GROUP'
    CHANNEL = 'CHANNEL'
    PERSONAL = 'PERSONAL'
    
    @staticmethod
    def get_group_type_from_msg(msg: Message):
        
        try:
            if msg.chat.type == "group" or msg.chat.type == "supergroup":
                return EGroupType.GROUP
            elif msg.chat.type == "channel":
                return EGroupType.CHANNEL
            elif msg.chat.type == "private":
                return EGroupType.PERSONAL
            else:
                return "None";
        except Exception as e:
            print(f"{Fore.RED}[ERROR get_group_type_from_msg]{Fore.BLACK}", msg)
            raise e;
    
    @staticmethod
    def get_emoji(chat_type: str):
        if chat_type == EGroupType.GROUP:
            return '👥'
        elif chat_type == EGroupType.CHANNEL:
            return '📢'
        else:
            return '🧍'
    
    @staticmethod
    def get_group_title_from_msg(msg: Message):
        group_type = EGroupType.get_group_type(msg)
        if group_type == EGroupType.GROUP or group_type == EGroupType.CHANNEL:
            return msg.chat.title
        else:
            return f'@{msg.from_user.username}'
    
    @staticmethod
    def get_group_type_from_str(group_type: str):
        if group_type == "GROUP":
            return EGroupType.GROUP
        elif group_type == "CHANNEL":
            return EGroupType.CHANNEL
        elif group_type == "PERSONAL":
            return EGroupType.PERSONAL
        else:
            return None
        

class Group(BaseModel):
    __tablename__ = "groups"

    id = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid4)
    tg_id = Column(BigInteger, unique=True, nullable=False)
    title = Column(VARCHAR(32), nullable=True)
    
    status = Column(VARCHAR(32), nullable=False, default=EGroupStatus.ACTIVE)
    chat_type = Column(VARCHAR(32), nullable=False, default=EGroupType.GROUP)
    # `Date the group was added (UTC, like history.time). Old groups: date of the first operation, or NULL
    created_at = Column(DateTime, nullable=True, default=datetime.datetime.utcnow, server_default=func.now())

    assigners = relationship("Assigner", back_populates="group", primaryjoin="Group.id==Assigner.group_id")
    accounts = relationship("Account", back_populates="group", primaryjoin="Group.id==Account.group_id")
    histories = relationship("History", back_populates="group", primaryjoin="Group.id==History.group_id")
    
    def __str__(self) -> str:
        return f'GROUP_MODEL ::: {self.tg_id} | {self.chat_type} | {self.title}';

    def __repr__(self) -> str:
        return f'GROUP_MODEL ::: {self.tg_id} | {self.chat_type} | {self.title}';