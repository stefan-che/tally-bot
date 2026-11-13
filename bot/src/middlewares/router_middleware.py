from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from colorama import Fore
import json
from typing import Callable, Awaitable, Any, Dict

from src.handlers.chat_members.new_chat_member import new_chat_member
from src.handlers.chat_members.left_chat_member import left_chat_member

class RouterMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # --- pre-handler logic (runs for Message events only) ---
        if isinstance(event, Message):
            msg = event

            # $ MIGRATE TO SUPERGROUP: handled by the registered handler
            #   (src/commands/router/migrate_groups.py), not here, to avoid a double run.

            # $ NEW CHAT MEMBER
            if msg.new_chat_members:
                for member in msg.new_chat_members:
                    await new_chat_member(msg, member)


            # $ LEFT CHAT MEMBER
            elif msg.left_chat_member:
                await left_chat_member(msg, msg.left_chat_member)

        return await handler(event, data)
