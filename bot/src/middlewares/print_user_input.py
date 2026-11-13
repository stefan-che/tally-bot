from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from colorama import Fore
import json
from datetime import datetime as time
from typing import Callable, Awaitable, Any, Dict

class PrintUserInputMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # --- pre-handler logic (runs for Message events only) ---
        if isinstance(event, Message):
            message = event
            print(f'\n{Fore.BLACK}===================================\n{Fore.MAGENTA}[MSG_FROM]{Fore.BLACK} {time.now()}')
            print(f'   {Fore.BLUE}USER: \t{Fore.GREEN}{message.from_user.username}')
            print(f'   {Fore.BLUE}USER_ID: \t{Fore.GREEN}{message.from_user.id}')
            print(f'   {Fore.BLUE}CHAT: \t{Fore.CYAN}{message.chat.username} | {message.chat.first_name} | {message.chat.full_name}')
            print(f'   {Fore.BLUE}Message: \t{Fore.YELLOW}{message.text}')

            if message.caption: print(f'   {Fore.BLUE}CAPTION: \t{Fore.YELLOW}{message.caption}')

            print(Fore.BLACK)

            if not message.text and not message.caption:
                print(f'\t{Fore.LIGHTBLUE_EX}:MSG:{Fore.LIGHTMAGENTA_EX} {message}')
                print(f'\t{Fore.LIGHTBLUE_EX}:data:{Fore.LIGHTMAGENTA_EX} {data}')
                print(f'\n{Fore.MAGENTA}[MSG_FROM]{Fore.LIGHTRED_EX}[END]\n{Fore.BLACK}==================================={Fore.BLACK}')

        return await handler(event, data)
