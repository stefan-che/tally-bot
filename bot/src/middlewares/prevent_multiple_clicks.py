from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, TelegramObject
from colorama import Fore
from typing import Callable, Awaitable, Any, Dict

class PreventMultipleClicksMiddleware(BaseMiddleware):
    def __init__(self):
        self._configured = False  # initialize _configured
        self.processing_states = {}  # Dictionary to store processing state for each user

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # --- callback pre-handler + post-handler logic ---
        if isinstance(event, CallbackQuery):
            query = event

            # --- pre-process ---
            user_id = query.from_user.id
            print(f'{Fore.BLUE}Update Id: {Fore.YELLOW}{query.id}{Fore.BLACK}')
            if user_id in self.processing_states and self.processing_states[user_id]:
                print(f'{Fore.LIGHTYELLOW_EX}[PRE Button is already being processed] {Fore.BLACK}callback :: {Fore.LIGHTRED_EX}{query.data}{Fore.BLACK}')
                await query.answer("Double click...")
                raise Exception("Double click...")

            # Set the processing state
            print(f'{Fore.BLUE}[PRE Proccess BTN] {Fore.LIGHTYELLOW_EX}{query.from_user.username} {Fore.BLACK}callback :: {Fore.LIGHTRED_EX}{query.data}{Fore.BLACK}')
            self.processing_states[user_id] = True

            try:
                result = await handler(event, data)
            finally:
                # --- post-process --- (also on error: otherwise every next button of the user hits "Double click...")
                self.processing_states[user_id] = False
            print(f'{Fore.GREEN}[Post Process COMPLETED] {Fore.BLACK}callback :: {Fore.LIGHTRED_EX}{query.data}{Fore.BLACK}')
            return result

        return await handler(event, data)
