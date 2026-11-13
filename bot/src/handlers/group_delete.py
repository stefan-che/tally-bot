from colorama import Fore
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from db import session_maker, EUserRole
from db.query.user import get_user_by_id_with_session
from db.query.group import lock_group_by_tg_id, delete_group_with_data
from src.utils.group_delete import CONFIRM, parse_gdel_callback, is_gdel_callback, build_delete_result
from src.utils.telegram import edit_message

__all__ = ["group_delete_callback", "is_gdel_callback"]


async def group_delete_callback(callback_query: CallbackQuery):
    """Confirmation buttons of /delete_group: "🗑 Yes, delete" / "Cancel".

    The super admin is checked again in the DB: everyone in the group sees the button, and callback_data can be forged.
    """
    message = callback_query.message
    if message is None:
        return await callback_query.answer()

    text = None
    try:
        user = await get_user_by_id_with_session(callback_query.from_user.id)
        if not (user and user.role and EUserRole.is_super_admin(user.role)):
            return await callback_query.answer("Only a super admin can delete groups", show_alert=True)

        parsed = parse_gdel_callback(callback_query.data)
        if parsed is None:
            return await callback_query.answer("This button is outdated")
        action, tg_id = parsed

        if action != CONFIRM:
            text = "Deletion cancelled"
        else:
            async with session_maker() as session:
                async with session.begin():
                    group = await lock_group_by_tg_id(session, tg_id)
                    result = await delete_group_with_data(session, group.id) if group else None
            text = build_delete_result(**result) if result else "The group is already deleted"
            if result:
                print(f"{Fore.YELLOW}[group_delete] {tg_id} by {callback_query.from_user.id}: {result}{Fore.BLACK}")

        await edit_message(text, message.chat.id, message.message_id)  # no keyboard: the buttons are removed
        await callback_query.answer()
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback_query.answer()
        else:
            print(f"{Fore.RED}[group_delete_callback] {e}{Fore.BLACK}")
            await callback_query.answer(text or "Could not update the message", show_alert=bool(text))
    except Exception as e:  # do not leave the button hanging
        print(f"{Fore.RED}[group_delete_callback] {e}{Fore.BLACK}")
        await callback_query.answer("Could not delete the group", show_alert=True)
