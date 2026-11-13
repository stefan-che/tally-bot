"""Group deletion with confirmation: callback_data and texts (pure functions, no db/aiogram).

  gdel:y:<tg_id> — "🗑 Yes, delete"
  gdel:n:<tg_id> — "Cancel"
"""
from html import escape

GDEL_CALLBACK_PREFIX = "gdel:"
CONFIRM, CANCEL = "y", "n"
ACCOUNTS_LIST_LIMIT = 15

WARNING = ("⚠️ This permanently deletes the group, all its accounts (with balances), the whole operation history "
           "and the user assignments. This cannot be undone.")


def build_gdel_callback(action: str, tg_id: int) -> str:
    return f"{GDEL_CALLBACK_PREFIX}{action}:{int(tg_id)}"


def parse_gdel_callback(data: str | None):
    """-> (action, tg_id), or None if the data is malformed."""
    if not is_gdel_callback(data):
        return None
    parts = data[len(GDEL_CALLBACK_PREFIX):].split(":")
    if len(parts) != 2 or parts[0] not in (CONFIRM, CANCEL):
        return None
    try:
        return parts[0], int(parts[1])
    except ValueError:
        return None


def is_gdel_callback(data: str | None) -> bool:
    return bool(data) and data.startswith(GDEL_CALLBACK_PREFIX)


def fmt_balance(amount, decimal=2) -> str:
    """1234567.5 -> 1’234’567.50; trailing fractional zeros are dropped."""
    try:
        decimal = min(max(int(decimal), 0), 8)
    except (TypeError, ValueError):
        decimal = 2
    text = f"{(amount or 0):,.{decimal}f}".replace(",", "’")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def build_delete_summary(title, tg_id: int, users: int, accounts, operations: int,
                         limit: int = ACCOUNTS_LIST_LIMIT) -> str:
    """accounts — [(currency, amount, decimal), ...]."""
    name = escape(str(title)) if title else "untitled"
    text = f"<b>Delete the group?</b>\n\n<b>{name}</b> <code>{int(tg_id)}</code>\n"
    text += f"<b>Users:</b> {users}\n"
    text += f"<b>Accounts:</b> {len(accounts)}\n"
    for currency, amount, decimal in accounts[:limit]:
        text += f"  • {escape(str(currency))}: <code>{fmt_balance(amount, decimal)}</code>\n"
    if len(accounts) > limit:
        text += f"  … and {len(accounts) - limit} more\n"
    text += f"<b>Operations in history:</b> {operations}\n\n"
    return text + WARNING


def build_delete_result(accounts: int, operations: int, users: int) -> str:
    return f"Group deleted. Removed: {accounts} accounts, {operations} operations, {users} users."
