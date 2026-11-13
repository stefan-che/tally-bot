from aiogram import types
from aiogram.types import InlineKeyboardButton, LinkPreviewOptions
from aiogram.utils.keyboard import InlineKeyboardBuilder
from db import session_maker, EGroupType
from db.query.account import get_all_accounts_with_groups
from db.query.history import get_last_message_ids
from src.utils.group_links import resolve_basic_group_links
from src import answer
from src.common import accounts_inline_btns
from src.utils.filter_acc_by_string import get_filter_accounts
from src.utils.sort_accounts import sort_accounts, normalize_sort, toggle_target, DEFAULT_SORT, SORT_NAME
from src.utils.accounts_pages import (
    build_all_callback, MAX_TEXT_LEN, VIEW_GROUPS, normalize_view, toggle_view, view_label,
)
from src.utils.accounts_layout import (
    GroupInfo, group_label, group_link, is_basic_group_id, flat_text, pack_flat, pack_grouped, grouped_text, visible_len,
)

NO_ACCOUNTS = "You have no accounts yet"
NO_MATCHING_ACCOUNTS = "No matching accounts"
PAGE_TRIMMED = "\n<i>…some accounts of this page did not fit into the message — refine the filter.</i>"
FILTER_TOO_LONG = "\n\n<i>The filter is too long for the buttons — only the first page is shown.</i>"
NO_PREVIEW = LinkPreviewOptions(is_disabled=True)


def _sort_button_label(mode: str) -> str:
    """Short label: two buttons per row."""
    return "💰 By amount" if normalize_sort(mode) == SORT_NAME else "🔤 By name"


def build_all_accounts_keyboard(mode: str, page: int, pages: int, filter_str: str | None, view: str | None = None):
    kb = InlineKeyboardBuilder()

    # 1. Sort and view (both reset to page 1)
    top = [
        InlineKeyboardButton(text=label, callback_data=data)
        for label, data in (
            (_sort_button_label(mode), build_all_callback(toggle_target(mode), 1, filter_str, view)),
            (view_label(view), build_all_callback(mode, 1, filter_str, toggle_view(view))),
        )
        if data
    ]
    if top:
        kb.row(*top)

    # 2. Pages: ⏮ 1 · ◀️ N-1 · N+1 ▶️ · last ⏭ (only the ones that make sense)
    targets = []
    if page > 2:
        targets.append(("⏮ 1", 1))
    if page > 1:
        targets.append((f"◀️ {page - 1}", page - 1))
    if page < pages:
        targets.append((f"{page + 1} ▶️", page + 1))
    if page < pages - 1:
        targets.append((f"{pages} ⏭", pages))
    nav = [
        InlineKeyboardButton(text=label, callback_data=data)
        for label, target in targets
        if (data := build_all_callback(mode, target, filter_str, view))
    ]
    if nav:
        kb.row(*nav)

    # 3. Statements
    for key, text in accounts_inline_btns.items():
        kb.row(InlineKeyboardButton(text=text, callback_data=f"admin.{key}"))
    return kb.as_markup()


def _group_info(group, message_id=None, resolved: dict | None = None) -> GroupInfo:
    if group is None:
        return GroupInfo("?")
    resolved = resolved or {}
    link = group_link(group.chat_type, group.tg_id, message_id, group.title) or resolved.get(group.tg_id)
    return GroupInfo(group_label(group.title, group.tg_id), EGroupType.get_emoji(group.chat_type), link)


async def _page_group_infos(session, groups: dict, page_ids) -> dict:
    """GroupInfo with ↗ links, only for the groups on the current page: one history query
    + Telegram API for old basic groups (cached, see group_links)."""
    page_ids = list(dict.fromkeys(page_ids))
    msg_ids = await get_last_message_ids(session, page_ids)
    basic_ids = [g.tg_id for gid in page_ids if (g := groups.get(gid)) is not None and is_basic_group_id(g.tg_id)]
    resolved = await resolve_basic_group_links(basic_ids)
    return {gid: _group_info(groups.get(gid), msg_ids.get(gid), resolved) for gid in page_ids}


def _trim_flat(page_accounts, infos, header):
    """Length guard (by visible text, as Telegram counts it) for very long account names."""
    text = flat_text(page_accounts, infos, header)
    if visible_len(text) <= MAX_TEXT_LEN:
        return text
    while len(page_accounts) > 1 and visible_len(text) > MAX_TEXT_LEN - visible_len(PAGE_TRIMMED):
        page_accounts = page_accounts[:-1]
        text = flat_text(page_accounts, infos, header)
    return text + PAGE_TRIMMED


async def build_all_accounts_view(session, filter_str: str | None = None, mode: str | None = None,
                                  page: int = 1, view: str | None = None):
    """Text and keyboard of a "get_all" page. -> (text, markup) or (error message, None)."""
    mode = normalize_sort(mode or DEFAULT_SORT)
    view = normalize_view(view)
    accounts = await get_all_accounts_with_groups(session)
    if not accounts:
        return NO_ACCOUNTS, None

    if filter_str:
        accounts = list(dict.fromkeys(get_filter_accounts(accounts, filter_str.split())))
        if not accounts:
            return NO_MATCHING_ACCOUNTS, None

    total = len(accounts)
    accounts = sort_accounts(accounts, mode)
    groups = {acc.group_id: acc.group for acc in accounts}

    labels = {gid: (group_label(g.title, g.tg_id) if g else "?") for gid, g in groups.items()}
    if view == VIEW_GROUPS:
        all_pages, aw = pack_grouped(accounts, labels)
        pages = len(all_pages)
        page = min(max(1, page), pages)
        blocks = all_pages[page - 1]
        infos = await _page_group_infos(session, groups, (key for key, _, _ in blocks))
        stats = f"groups {len(groups)} · accounts {total}"
        header = (f"<code>Funds by group: page {page}/{pages} · {stats}</code>\n" if pages > 1
                  else f"<code>Funds by group · {stats}</code>\n")
        text = grouped_text(blocks, infos, aw, header)
    else:
        all_pages = pack_flat(accounts, labels)
        pages = len(all_pages)
        page = min(max(1, page), pages)
        page_accounts = all_pages[page - 1]
        infos = await _page_group_infos(session, groups, (acc.group_id for acc in page_accounts))
        header = f"<code>Your funds: page {page}/{pages} · total {total}</code>\n" if pages > 1 else "<code>Your funds:</code>\n"
        text = _trim_flat(page_accounts, infos, header)

    if pages > 1 and filter_str and build_all_callback(mode, page, filter_str, view) is None:
        text += FILTER_TOO_LONG
    return text, build_all_accounts_keyboard(mode, page, pages, filter_str, view)


# # GET_ALL (super admin, private chat with the bot only — checked in router/get_all.py)
async def get_accounts(msg: types.Message):
    data = msg.text.strip().split()
    filter_str = " ".join(data[1:]) or None  # get_all [filter1] [filter2]

    async with session_maker() as session:
        text, markup = await build_all_accounts_view(session, filter_str)
    await answer(msg, text, reply_markup=markup, link_preview_options=NO_PREVIEW)
