#!/usr/bin/env python3
"""
Manage the Telegram webhook.

Usage:
  python3 webhook.py set     — register the webhook
  python3 webhook.py delete  — delete the webhook
  python3 webhook.py info    — show the current webhook settings

Environment variables (from .env):
  BOT_TOKEN       — bot token (required)
  WEBHOOK_HOST    — public HTTPS address (required for set)
  WEBHOOK_PATH    — webhook path (default /webhook/telegram)
  WEBHOOK_SECRET  — secret token (optional)
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "").rstrip("/")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook/telegram")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")


async def cmd_set():
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN is not set in .env")
        sys.exit(1)
    if not WEBHOOK_HOST:
        print("ERROR: WEBHOOK_HOST is not set in .env")
        sys.exit(1)

    from aiogram import Bot
    bot = Bot(BOT_TOKEN)

    webhook_url = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
    kwargs = {"url": webhook_url}
    if WEBHOOK_SECRET:
        kwargs["secret_token"] = WEBHOOK_SECRET

    try:
        await bot.set_webhook(**kwargs)
        print(f"OK  Webhook set: {webhook_url}")
        if WEBHOOK_SECRET:
            print(f"    Secret token: configured")
        else:
            print(f"    Secret token: not set (consider adding WEBHOOK_SECRET)")
    finally:
        await bot.session.close()


async def cmd_delete():
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN is not set in .env")
        sys.exit(1)

    from aiogram import Bot
    bot = Bot(BOT_TOKEN)

    try:
        await bot.delete_webhook()
        print("OK  Webhook deleted")
    finally:
        await bot.session.close()


async def cmd_info():
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN is not set in .env")
        sys.exit(1)

    from aiogram import Bot
    bot = Bot(BOT_TOKEN)

    try:
        info = await bot.get_webhook_info()
        if info.url:
            print(f"URL            : {info.url}")
            print(f"Pending updates: {info.pending_update_count}")
            print(f"Max connections: {info.max_connections}")
            print(f"Has secret     : {info.has_custom_certificate}")
            if info.last_error_message:
                print(f"Last error     : {info.last_error_message}")
                print(f"Last error date: {info.last_error_date}")
        else:
            print("No webhook is set (polling mode)")
    finally:
        await bot.session.close()


COMMANDS = {
    "set": cmd_set,
    "delete": cmd_delete,
    "info": cmd_info,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print("Usage: python3 webhook.py <set|delete|info>")
        sys.exit(1)

    asyncio.run(COMMANDS[sys.argv[1]]())


if __name__ == "__main__":
    main()
