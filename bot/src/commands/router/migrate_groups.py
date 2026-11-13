from html import escape

from colorama import Fore
from aiogram import types
from src.utils.access import getRole
from myTypes.roles import Role
from src.utils.telegram import answer
from src.utils.group_migration import migrate_group_tg_id
from ..admin.migrate_group import migrate_groups as migrate_groups_auto


async def migrate_groups(msg: types.Message):
    # $ Service messages. Telegram sends two per migration; both are handled
    #   idempotently and silently (no text into the client group).
    if msg.migrate_to_chat_id:      # arrives in the OLD (dead) chat
        old_chat, new_chat = msg.chat.id, msg.migrate_to_chat_id
        print(f"{Fore.LIGHTRED_EX}migrate_to_chat_id{Fore.GREEN} '{old_chat}' {Fore.BLUE}-> {Fore.LIGHTGREEN_EX}'{new_chat}' {Fore.BLACK}")
        await migrate_groups_auto(msg, old_chat, new_chat)
        return
    if msg.migrate_from_chat_id:    # arrives in the NEW supergroup
        old_chat, new_chat = msg.migrate_from_chat_id, msg.chat.id
        print(f"{Fore.LIGHTRED_EX}migrate_from_chat_id{Fore.GREEN} '{old_chat}' {Fore.BLUE}-> {Fore.LIGHTGREEN_EX}'{new_chat}' {Fore.BLACK}")
        await migrate_groups_auto(msg, old_chat, new_chat)
        return

    # $ Manual command: /migrate <old_chat_id> [<new_chat_id>] (super-admin)
    data = (msg.text or "").lower().split()
    new_chat = msg.chat.id
    try:
        if len(data) == 2:
            old_chat = int(data[1])
        elif len(data) == 3:
            if await getRole(msg.from_user.id) != Role.OWNER:
                return await answer(msg, "Bot owner only")
            old_chat, new_chat = int(data[1]), int(data[2])
        else:
            return await answer(msg, "Specify the previous Chat_ID to migrate from: /migrate &lt;old_chat_id&gt;")
    except ValueError:
        return await answer(msg, "Chat_ID must be a number")

    result = await migrate_group_tg_id(old_chat, new_chat)
    icon = "✅" if result.ok and not result.conflicts else "⚠️"
    await answer(msg, f"{icon} Migration: <code>{escape(result.summary())}</code>")
