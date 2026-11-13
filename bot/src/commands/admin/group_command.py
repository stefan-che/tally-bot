from html import escape
from aiogram.types import Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from db import Group, EGroupType, EGroupStatus, User, session_maker
from db.query.group import (
    get_group_by_tg_id, create_group, get_all_groups, get_all_groups, count_groups_filtered, get_groups_page,
    get_group_delete_stats,
)
from db.query.history import get_last_message_ids
from src.utils.group_links import resolve_basic_group_links
from src.utils.accounts_layout import group_link, is_basic_group_id
from src.utils.groups_pages import (
    GROUPS_PER_PAGE, STATUSES, TYPES, ACCOUNTS, USERS, SORTS, DIRS, STATUS_LABELS, TYPE_LABELS, ACCOUNTS_LABELS,
    USERS_LABELS, SORT_LABELS, DIR_LABELS, STATUS_VALUES, TYPE_VALUES, PRESENCE_VALUES, SORT_FIELDS,
    normalize_filters, cycle, fit_search, clamp_page, build_groups_callback,
)
from src.utils.group_delete import CONFIRM, CANCEL, build_gdel_callback, build_delete_summary
from src.commands.admin.get import NO_PREVIEW
from db.query.assigner import get_assigners_by_group_id
from src import answer
from app.utils import visualise

SEARCH_TRIMMED = "\n<i>The search is too long for the buttons — trimmed.</i>"

async def add_group(msg: Message):
    data = msg.text.strip().split()
    chat_type = EGroupType.get_group_type_from_msg(msg)
    
    async with session_maker() as session:
        async with session.begin():
            if len(data) == 1 and chat_type == EGroupType.GROUP:
                group_tg_id = msg.chat.id
                group = await get_group_by_tg_id(session, group_tg_id)
                if group:
                    return await answer(msg, "The group is already added")
                else:
                    title = msg.chat.title;
                    group = await create_group(session, group_tg_id, chat_type, title=title)
                    return await answer(msg, "Group created")
                
            elif len(data) == 2:
                try:
                    group_tg_id = int(data[1])
                except Exception:
                    return await answer(msg, "Check your input\n/add_group [group_id]\nwhere group_id must be a number")
                
                group = await get_group_by_tg_id(session, group_tg_id)
                if group:
                    return await answer(msg, "The group is already added")
                else:
                    group = await create_group(session, group_tg_id, chat_type)
                    return await answer(msg, "Group created")
            
            else:
                if chat_type == EGroupType.GROUP:
                    return await answer(msg, "Check your input\n/add_group")
                else:
                    return await answer(msg, "Check your input\n/add_group [group_id]")
                

# yield by 10 groups
def yield_groups(groups, step=10):
    for i in range(0, len(groups), step):
        yield groups[i:i+10]

async def get_groups(msg: Message):
    req_chat_type = EGroupType.get_group_type_from_msg(msg);

    # * Private chat: one message with paging, search and filters (/groups [search])
    if req_chat_type == EGroupType.PERSONAL:
        search = " ".join((msg.text or "").strip().split()[1:]) or None
        fitted = fit_search(search)
        async with session_maker() as session:
            text, markup = await build_groups_view(session, search=fitted)
        if search and fitted != search:
            text += SEARCH_TRIMMED
        return await answer(msg, text, reply_markup=markup, link_preview_options=NO_PREVIEW)

    # * Group chat: only this group
    async with session_maker() as session:
            group = await get_group_by_tg_id(session, msg.chat.id, populateAssigners=True, populateAccounts=True)
            groups = [group] if group else []

            if not groups:
                return await answer(msg, "No groups found")
            for filtered_group in yield_groups(groups):
                text = "<b>Group:</b>"
                text += "\n"
                for group in filtered_group:
                    chat_type = EGroupType.get_emoji(group.chat_type)
                    status = EGroupStatus.get_emoji(group.status)
                    text += f"\n  {status} {chat_type} <b>{escape(str(group.title))}</b> <code>{group.tg_id}</code>\n"
                    if group.assigners:
                        text += f"               <b>Users:</b> {len(group.assigners)}\n"
                    if group.accounts:
                        text += f"               <b>Accounts:</b> {len(group.accounts)}\n"
                await answer(msg, text)


def _groups_row(group, users: int, accounts: int, link: str | None) -> str:
    chat_type = EGroupType.get_emoji(group.chat_type)
    status = EGroupStatus.get_emoji(group.status)
    title = f"<b>{escape(str(group.title))}</b>"
    if link:
        title = f'<a href="{escape(link, quote=True)}">{title}</a>'
    text = f"\n  {status} {chat_type} {title} <code>{group.tg_id}</code>\n"
    if users:
        text += f"               <b>Users:</b> {users}\n"
    if accounts:
        text += f"               <b>Accounts:</b> {accounts}\n"
    return text


async def _page_links(session, groups) -> dict:
    """{group.id: link} — only for the groups on the current page (Telegram API only for old basic groups, cached)."""
    msg_ids = await get_last_message_ids(session, [g.id for g in groups])
    resolved = await resolve_basic_group_links([g.tg_id for g in groups if is_basic_group_id(g.tg_id)])
    links = {}
    for g in groups:
        link = group_link(g.chat_type, g.tg_id, msg_ids.get(g.id), g.title) or resolved.get(g.tg_id)
        if link:
            links[g.id] = link
    return links


def build_groups_keyboard(page: int, pages: int, status: str, chat_type: str, accounts: str, search: str | None,
                          users: str = None, sort: str = None, direction: str = None):
    status, chat_type, accounts, users, sort, direction = normalize_filters(
        status, chat_type, accounts, users, sort, direction)
    state = dict(status=status, chat_type=chat_type, accounts=accounts, users=users, sort=sort, direction=direction,
                 search=search)

    def cb(target_page, **changes):
        return build_groups_callback(target_page, **{**state, **changes})

    def buttons(items):
        return [InlineKeyboardButton(text=label, callback_data=data) for label, data in items if data]

    kb = InlineKeyboardBuilder()

    # 1. Cycling filters (reset to page 1), 2 per row so they fit on a phone
    filter_rows = (
        ((STATUS_LABELS[status], cb(1, status=cycle(status, STATUSES))),
         (TYPE_LABELS[chat_type], cb(1, chat_type=cycle(chat_type, TYPES)))),
        ((ACCOUNTS_LABELS[accounts], cb(1, accounts=cycle(accounts, ACCOUNTS))),
         (USERS_LABELS[users], cb(1, users=cycle(users, USERS)))),
        # 2. Sorting: cycling field + direction
        ((SORT_LABELS[sort], cb(1, sort=cycle(sort, SORTS))),
         (DIR_LABELS[direction], cb(1, direction=cycle(direction, DIRS)))),
    )
    for items in filter_rows:
        if row := buttons(items):
            kb.row(*row)

    # 3. Pages: ◀️ N/M ▶️
    if pages > 1:
        nav = []
        if page > 1:
            nav.append(("◀️", cb(page - 1)))
        nav.append((f"{page}/{pages}", cb(page)))
        if page < pages:
            nav.append(("▶️", cb(page + 1)))
        if row := buttons(nav):
            kb.row(*row)
    return kb.as_markup()


async def build_groups_view(session, page: int = 1, status: str = None, chat_type: str = None,
                            accounts: str = None, search: str | None = None,
                            users: str = None, sort: str = None, direction: str = None):
    """Text and keyboard of a /groups page in a private chat. -> (text, markup)."""
    status, chat_type, accounts, users, sort, direction = normalize_filters(
        status, chat_type, accounts, users, sort, direction)
    filter_args = dict(
        search=search,
        status=STATUS_VALUES.get(status),
        chat_type=TYPE_VALUES.get(chat_type),
        has_accounts=PRESENCE_VALUES.get(accounts),
        has_users=PRESENCE_VALUES.get(users),
    )
    total = await count_groups_filtered(session, **filter_args)
    page, pages, offset = clamp_page(page, total)
    rows = await get_groups_page(session, offset, GROUPS_PER_PAGE, **filter_args,
                                 sort=SORT_FIELDS[sort], descending=direction == "d") if total else []
    markup = build_groups_keyboard(page, pages, status, chat_type, accounts, search, users, sort, direction)

    header = "<b>Groups:</b>"
    if search:
        header += f" search \"{escape(search)}\""
    header += f"\n<code>Found: {total}" + (f" · page {page}/{pages}" if pages > 1 else "") + "</code>\n"

    if not rows:
        return header + "\nNo groups found", markup

    links = await _page_links(session, [g for g, _, _ in rows])
    text = header + "".join(_groups_row(g, u, a, links.get(g.id)) for g, u, a in rows)
    return text, markup


def build_delete_keyboard(tg_id: int):
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="🗑 Yes, delete", callback_data=build_gdel_callback(CONFIRM, tg_id)),
        InlineKeyboardButton(text="Cancel", callback_data=build_gdel_callback(CANCEL, tg_id)),
    )
    return kb.as_markup()


async def delete_group(msg: Message):
    """/delete_group [group_id] — deletes nothing by itself: shows what will be deleted and asks for confirmation with a button."""
    data = msg.text.strip().split()
    if len(data) == 1:
        group_tg_id = msg.chat.id
    elif len(data) == 2:
        try:
            group_tg_id = int(data[1])
        except Exception:
            return await answer(msg, "Check your input\n/delete_group [group_id]\nwhere group_id must be a number")
    else:
        return await answer(msg, "Check your input\n/delete_group [group_id]")

    async with session_maker() as session:
        group = await get_group_by_tg_id(session, group_tg_id)
        if not group:
            return await answer(msg, "Group not found")
        users, accounts, operations = await get_group_delete_stats(session, group.id)
        text = build_delete_summary(group.title, group.tg_id, users, accounts, operations)
    return await answer(msg, text, reply_markup=build_delete_keyboard(group_tg_id))


async def change_group_type(msg: Message):
    data = msg.text.strip().split()
    
    async with session_maker() as session:
        async with session.begin():
            if len(data) == 3:
                try:
                    group_tg_id = int(data[1])
                    chat_type = EGroupType.get_group_type_from_str(data[2])
                    
                    if not chat_type:
                        return await answer(msg, f"Invalid group type {data[2]}")
                    
                except Exception:
                    return await answer(msg, "Check your input\n/change_group_type [group_id] [group_type]\nwhere group_id must be a number")
                
                group = await get_group_by_tg_id(session, group_tg_id)
                if group:
                    group.chat_type = chat_type
                    return await answer(msg, "Group type changed")
                else:
                    return await answer(msg, "Group not found")
            else:
                return await answer(msg, "Check your input\n/change_group_type [group_id] [group_type]")
            
async def get_group(msg: Message):
    data = msg.text.strip().split()

    async with session_maker() as session:
        async with session.begin():
            if len(data) == 1:
                group = await get_group_by_tg_id(session, msg.chat.id, populateAssigners=True, populateAccounts=True)
                if group:
                    text = _get_group_text(group)
                    return await answer(msg, text)
                else:
                    return await answer(msg, "Group not found")
            elif len(data) == 2:
                try:
                    group_tg_id = int(data[1])
                except Exception:
                    return await answer(msg, "Check your input\n/group [group_id]\nwhere group_id must be a number")
                
                group = await get_group_by_tg_id(session, group_tg_id, populateAssigners=True, populateAccounts=True)
                if group:
                    text = _get_group_text(group)
                    return await answer(msg, text)
                else:
                    return await answer(msg, "Group not found")
            else:
                return await answer(msg, "Check your input\n/group [group_id]")
            
def _get_group_text(group):
    chat_type = EGroupType.get_emoji(group.chat_type)
    status = EGroupStatus.get_emoji(group.status)
    text = ""
    
    text += f"\n  {status} {chat_type} <b>{escape(str(group.title))}</b> <code>{group.tg_id}</code>\n"
    if group.assigners:
        text += f"               <b>Users:</b> {len(group.assigners)}\n"
    if group.accounts:
        text += f"               <b>Accounts:</b> {len(group.accounts)}\n"
        
    return text