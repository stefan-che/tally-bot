import signal
from colorama import Fore
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage # FSM
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from src.commands import register_commands
from src.handlers import register_handlers
from src.handlers.calculate import calculate
from src.FCM import register_scenes
from src.middlewares.prevent_multiple_clicks import PreventMultipleClicksMiddleware
from src.middlewares.print_user_input import PrintUserInputMiddleware
from src.middlewares.router_middleware import RouterMiddleware
from src.middlewares.guard_middleware import GuardMiddleware
from dotenv import load_dotenv
from src.app.app_state import AppState
from db import session_maker
from app.api import create_app
from aiohttp import web

import os
import asyncio

load_dotenv();
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = os.getenv("OWNER_ID")
USE_GUARD = os.getenv("USE_GUARD")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "").rstrip("/")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook/telegram")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
DEBUG_PRINT_INPUT = os.getenv("DEBUG_PRINT_INPUT", "") == "1"

async def main() -> None:
    print("Bot is Starting...", "token set" if BOT_TOKEN else "TOKEN NOT SET", OWNER_ID)
    bot = Bot(BOT_TOKEN)
    storage = MemoryStorage();

    await bot.send_message(OWNER_ID, "Tally bot is started...")
    me = await bot.get_me()
    print("ME:", me)
    dp = Dispatcher(storage=storage);

    app_state = AppState()
    app_state.init(bot, dp, session_maker=session_maker())
    
    # MIDDLEWARES
    prevent_clicks_middleware = PreventMultipleClicksMiddleware()  # Create an instance of the middleware
    supergroup_middlware = RouterMiddleware()

    # Printing incoming messages exposes user content in logs: off unless DEBUG_PRINT_INPUT=1.
    if DEBUG_PRINT_INPUT:
        print_input_middleware = PrintUserInputMiddleware()
        dp.message.middleware(print_input_middleware)
        dp.callback_query.middleware(print_input_middleware)
    dp.message.middleware(prevent_clicks_middleware)  # Set up the middleware instance
    dp.callback_query.middleware(prevent_clicks_middleware)  # Set up the middleware instance
    dp.message.middleware(supergroup_middlware)  # Set up the middleware instance
    dp.callback_query.middleware(supergroup_middlware)  # Set up the middleware instance

    if USE_GUARD and USE_GUARD.lower() == "true":
        print(f"{Fore.GREEN}Guard Middleware is Enabled")
        guard_middleware = GuardMiddleware()
        # aiogram 3: the guard inspects the whole Update (message / callback_query),
        # so it must be an outer middleware on the update observer.
        dp.update.outer_middleware(guard_middleware)
    else:
        print(f"{Fore.RED}Guard Middleware is Disabled: .env.USE_GUARD -> {Fore.LIGHTYELLOW_EX}'{USE_GUARD}'")


    register_commands()
    register_handlers(dp)
    register_scenes(dp);

    dp.message.register(calculate)

    api_port = int(os.getenv("API_PORT", 8080))

    use_webhook = bool(WEBHOOK_HOST)

    if use_webhook:
        webhook_url = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
        set_webhook_kwargs = {"url": webhook_url}
        if WEBHOOK_SECRET:
            set_webhook_kwargs["secret_token"] = WEBHOOK_SECRET
        await bot.set_webhook(**set_webhook_kwargs)
        print(f"{Fore.GREEN}Webhook mode: {webhook_url}")
    else:
        await bot.delete_webhook()
        print(f"{Fore.YELLOW}Polling mode (WEBHOOK_HOST not set)")

    app = create_app(dp if use_webhook else None)
    if use_webhook:
        SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=WEBHOOK_SECRET or None).register(app, path=WEBHOOK_PATH)
        setup_application(app, dp, bot=bot)
    api_runner = web.AppRunner(app, access_log=None)
    await api_runner.setup()
    await web.TCPSite(api_runner, "0.0.0.0", api_port).start()
    print(f"{Fore.GREEN}API server started on :{api_port}")

    if use_webhook:
        stop_event = asyncio.Event()

        def _handle_signal():
            stop_event.set()

        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, _handle_signal)

        await stop_event.wait()
        await bot.delete_webhook()
        await bot.session.close()
    else:
        await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main());
    except Exception as e:
        print(f'{Fore.YELLOW}ERROR:{Fore.RED}', e)
        print("Bot Was Stopped")
