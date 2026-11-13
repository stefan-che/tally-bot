from aiogram import BaseMiddleware
from aiogram.types import Update, TelegramObject
from sqlalchemy.exc import NoResultFound
from src.app.app_state import AppState
from typing import Callable, Awaitable, Any, Dict

class TelegramGuardMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # The original update-guard body runs first (below). Its `return`
        # meant "exit hook -> continue to handler" in aiogram 2, so extracting it
        # into a helper preserves behavior: normal completion falls through to the
        # handler.
        update = event
        await self._process_update(update, data)
        return await handler(event, data)

    async def _process_update(self, update: Update, data: dict):
        user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
        session_maker = AppState().session_maker

        # Find the current handler metadata
        current_handler = None
        for handler in AppState().handler_registry:
            if handler["function"].__name__ == data["handler"].__name__:
                current_handler = handler
                break

        # If the handler requires authorization, check the user
        if current_handler and current_handler["requires_auth"]:
            async with session_maker() as session:
                try:
                    result = await session.execute(f"SELECT * FROM users WHERE id = {user_id}")
                    user = result.fetchone()
                    if not user:
                        await update.message.answer("You are not registered.")
                        return
                    data["user"] = user
                except NoResultFound:
                    await update.message.answer("Database error occurred.")
