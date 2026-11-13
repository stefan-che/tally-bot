from html import escape

from colorama import Fore
from aiogram import types
from sqlalchemy import select

from db import session_maker, User, EUserRole
from src.utils.group_migration import migrate_group_tg_id, MigrationResult
from src.utils.telegram import send_message


async def notify_super_admins(text: str):
    """Problems with client groups go to super-admins in private, never into the client chat."""
    try:
        async with session_maker() as session:
            res = await session.execute(select(User.id).where(User.role == EUserRole.SUPER_ADMIN))
            admin_ids = res.scalars().all()
    except Exception as e:  # noqa: BLE001
        print(Fore.RED, "[notify_super_admins]", e)
        return
    for admin_id in admin_ids:
        try:
            await send_message(admin_id, text)
        except Exception as e:  # noqa: BLE001 - admin may have blocked the bot
            print(Fore.RED, f"[notify_super_admins] {admin_id}: {e}")


async def migrate_groups(msg: types.Message | None, old_group_id, new_group_id) -> MigrationResult:
    """Automatic migration (service message). Silent in the client group;
    super-admins are alerted only if something needs a human."""
    result = await migrate_group_tg_id(old_group_id, new_group_id)
    if not result.ok or result.conflicts:
        title = escape(msg.chat.title) if msg and msg.chat and msg.chat.title else ""
        await notify_super_admins(
            f"⚠️ <b>Group migration</b> {title}\n<code>{escape(result.summary())}</code>\n"
            f"To retry, run in the new group: <code>/migrate {result.old_id}</code>"
        )
    return result
