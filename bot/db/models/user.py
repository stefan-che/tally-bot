from colorama import Fore
from enum import Enum
from sqlalchemy import Column, VARCHAR, BigInteger,  ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import BaseModel
class EUserRole(str, Enum):
    USER = 'USER'
    ADMIN = 'ADMIN'
    SUPER_ADMIN = 'SUPER_ADMIN'

    @staticmethod
    def get_roles():
        return [role.upper() for role in EUserRole]
    
    @staticmethod
    def get_valid_role(role):
        if EUserRole.is_valid_role(role):
            return role.upper();
    

    @staticmethod
    def get_message_role(role):
        if role == EUserRole.USER:
            return "USR";
        elif role == EUserRole.ADMIN:
            return "ADM";
        elif role == EUserRole.SUPER_ADMIN:
            return "SPA";
        else:
            return "UNK";

    @staticmethod
    def is_valid_role(role: str):
        return role.upper() in EUserRole.get_roles()
    
    @staticmethod
    def is_roles(roles: list):
        return all([role.upper() in EUserRole.get_roles() for role in roles])

    @staticmethod
    def has_roles_access(role: str, roles: list = []):
        result = role.upper() in [*roles, EUserRole.SUPER_ADMIN];
        
        color = Fore.LIGHTGREEN_EX if result else Fore.LIGHTRED_EX;
        
        return role.upper() in [*roles, EUserRole.SUPER_ADMIN]
    
    @staticmethod
    def is_admin(role):
        return EUserRole.has_roles_access(role, [EUserRole.ADMIN])
    
    @staticmethod
    def is_super_admin(role):
        return EUserRole.has_roles_access(role)
    
    @staticmethod
    def is_one_of_all(role):
        return EUserRole.has_roles_access(role, EUserRole.get_roles())


class EUserStatus(str, Enum):
    ACTIVE = 'Active'
    INACTIVE = 'Inactive'
    NEW = 'New'

class User(BaseModel):
    __tablename__ = "users"

    # Telegram user id
    id = Column(BigInteger, primary_key=True,
                unique=True)
    # User name / nickname
    name = Column(VARCHAR(32), nullable=True)
    # User status
    status = Column(VARCHAR(32), nullable=False, default=EUserStatus.NEW);
    # User role
    role = Column(VARCHAR(32), nullable=False, default=EUserRole.USER);

    histories = relationship("History", back_populates="user", primaryjoin="User.id==History.user_id")
    assigners = relationship("Assigner", back_populates="user", primaryjoin="User.id==Assigner.user_id")

    def __str__(self) -> str:
        return f'USER ::: {self.id} | Name: {self.name} | Role: {self.role}';

    def __repr__(self) -> str:
        return f'USER ::: {self.id} | Name: {self.name} | Role: {self.role}';
