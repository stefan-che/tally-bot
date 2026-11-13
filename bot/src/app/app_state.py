from colorama import Fore
from aiogram.filters import Command
from db import EUserRole
from app.utils import visualise
class AppState:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppState, cls).__new__(cls)
            cls._instance.bot = None
            cls._instance.dp = None
            cls._instance.session_maker = None
            cls._instance._handler_registry = []  # Store metadata about handlers
        return cls._instance

    @classmethod
    def init(cls, bot, dp, session_maker):
        state = cls()
        state.bot = bot
        state.dp = dp
        state.session_maker = session_maker

    @property
    def handler_registry(self):
        return self._instance._handler_registry

    def add_command_with_hear_listeners(self, func, commands, is_public=False, roles=[], group_roles=[], private_roles=[]):
        self.add_command_listener(func, commands, is_public, roles, group_roles)
        self.add_hear_listener(func, commands, is_public, roles, group_roles)
        
    def add_command_listener(self, func, commands, is_public=False, roles=[], group_roles=[], private_roles=[]):
        self._instance._handler_registry.append({ "commands": commands, "is_public": is_public, "type": "command", "roles": roles, "group_roles": group_roles, "private_roles": private_roles })
        self._instance.dp.message.register(func, Command(commands=commands))

    def add_hear_listener(self, func, commands, is_public=False, roles=[], group_roles=[], private_roles=[]):
        self._instance._handler_registry.append({ "commands": commands, "is_public": is_public, "type": "hear", "roles": roles, "group_roles": group_roles, "private_roles": private_roles })
        self._instance.dp.message.register(func, lambda m: m.text and m.text.lower().split(" ")[0] in commands)
    
    def add_with_lambda_listener(self, func, lambda_func, is_public=False, roles=[], group_roles=[], private_roles=[]):
        self._instance._handler_registry.append({ "lambda_func": lambda_func, "is_public": is_public, "type": "lambda", "roles": roles, "group_roles": group_roles, "private_roles": private_roles })
        self._instance.dp.message.register(func, lambda m: lambda_func(m))

    
    def get_handler_by_condition(self, text: str):
        text = text.lower()
        for handler in self.handler_registry:
            
            handler_type = handler["type"]
            handler_commands = handler["commands"]
            
            
            
            
            if handler_type == "command": # TODO - replace with enum
                for command in handler_commands:
                    if text.startswith(f"/{command}"):
                        return handler
                    
            if handler_type == "hear":
                for hear in handler_commands:
                    if text.startswith(hear):
                        return handler
                    else:
                        pass
                        
            if "lambda_func" in handler and handler["lambda_func"]:
                if handler["lambda_func"](text):
                    return handler
    
    def is_user_has_access(self, user, handler):
        if not handler or len(handler["roles"]) == 0:
            return True
        else:
            return EUserRole.has_roles_access(user.role, handler["roles"])
        
    def is_user_has_private_access(self, user, handler):
        if handler:
            if len(handler["private_roles"]) == 0:
                return self.is_user_has_access(user, handler);
            else:
                return EUserRole.has_roles_access(user.role, handler["private_roles"]) or self.is_user_has_access(user, handler);
        else:
            return True
        
