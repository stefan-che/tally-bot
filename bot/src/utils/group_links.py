"""↗ links for old basic groups (id "-…" without -100) in "get_all".

Telegram gives no link for such a group id. We ask Telegram itself (getChat), only for the groups on the current page:
  - the group was upgraded to a supergroup → link to the new supergroup (t.me/c/<new id>/1);
  - the group has a public @username     → t.me/<username>;
  - the bot is an admin and the group has a primary invite link → that link;
  - otherwise (bot not in the group, no link) → no link.
Nothing is created or changed in the groups: export/createChatInviteLink is NOT called (the client would get new links).
Results are cached in process memory (no DB) so paging does not hit Telegram every time.
"""
import asyncio
import time

from aiogram.exceptions import TelegramMigrateToChat
from colorama import Fore

from src.utils.accounts_layout import supergroup_link
from src.utils.telegram import bot

FOUND_TTL = 6 * 3600   # a found link is kept for 6 h
MISS_TTL = 3600        # "no link" is rechecked hourly
REQUEST_TIMEOUT = 3    # seconds per getChat call
PARALLEL = 10          # concurrent requests (Telegram limit ~30/s)

_cache: dict[int, tuple[float, str | None]] = {}
_sem = asyncio.Semaphore(PARALLEL)


async def _resolve_one(tg_id: int) -> str | None:
    async with _sem:
        try:
            chat = await bot.get_chat(tg_id, request_timeout=REQUEST_TIMEOUT)
            if chat.username:
                return f"https://t.me/{chat.username}"
            return chat.invite_link or None
        except TelegramMigrateToChat as e:
            return supergroup_link(e.migrate_to_chat_id)
        except Exception as e:  # bot not in the group, timeout, etc. — just no link
            print(f"{Fore.YELLOW}[group_links] {tg_id}: {str(e)[:80]}{Fore.BLACK}")
            return None


async def resolve_basic_group_links(tg_ids) -> dict:
    """{tg_id: link} for the groups where one was found. Never raises."""
    now = time.monotonic()
    result, todo = {}, []
    for tg_id in dict.fromkeys(tg_ids):
        hit = _cache.get(tg_id)
        if hit and hit[0] > now:
            if hit[1]:
                result[tg_id] = hit[1]
        else:
            todo.append(tg_id)
    if todo:
        links = await asyncio.gather(*(_resolve_one(t) for t in todo))
        for tg_id, link in zip(todo, links):
            _cache[tg_id] = (now + (FOUND_TTL if link else MISS_TTL), link)
            if link:
                result[tg_id] = link
    return result
