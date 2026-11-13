"""Layout of "get_all" (super admin): two views of the same account list.

  flat   — flat list "amount currency ↗ group": amount and currency are aligned inside <code>, the link arrow and the
           group title use the normal font outside <code> (links are impossible inside <code>). Widths are per page.
  groups — by group: the group header (emoji + title + ↗) once, its accounts below it.
           Groups are ordered by title (amounts in different currencies are not summed), accounts by the chosen sort.
           Pages are split by group and by text budget; a long group continues with a "(cont.)" mark.

The Telegram 4096 limit counts VISIBLE text (after HTML parsing): tags and link URLs are not included.

Pure functions: no aiogram and no DB (tested directly).
"""
import re
from dataclasses import dataclass
from html import escape, unescape

from .sort_accounts import _natural_key

LINK_ARROW = "↗"
NO_LINK_MARK = "·"         # for groups without a link (old basic groups)
GROUP_LABEL_MAX = 20       # group title in normal font; longer ones get "…" (so the line does not wrap)
MAX_CURRENCY_PAD = 14      # currency column is at most this wide (p97 on real data); longer ones get "…" so the arrows stay aligned
NBSP = "\u00a0"            # spaces inside <code> are non-breaking: Telegram keeps trailing ones, the column width stays fixed
PAGE_TEXT_BUDGET = 3700   # visible characters per page: the 4096 limit minus the page header and notes
LINES_PER_PAGE = 30        # account lines per page (both views): a short list stays readable on screen
CONTINUED = " (cont.)"

_TAG = re.compile(r"<[^>]+>")


@dataclass(frozen=True)
class GroupInfo:
    label: str
    emoji: str = ""
    link: str | None = None


def visible_len(html: str) -> int:
    """Text length as Telegram counts it: without tags, with &amp; etc. unescaped."""
    return len(unescape(_TAG.sub("", html)))


def fmt_amount(amount) -> str:
    """As in get_accounts_message: no fractional part, ’ as the thousands separator."""
    return f"{(amount or 0):,.0f}".replace(",", "’")


def clip(text: str, width: int) -> str:
    text = text or ""
    if len(text) <= width:
        return text
    return "…" if width <= 1 else text[:width - 1] + "…"


def group_label(title, tg_id) -> str:
    return (title or "").strip() or str(tg_id)


_USERNAME = re.compile(r"[A-Za-z][A-Za-z0-9_]{3,31}")


def is_basic_group_id(tg_id) -> bool:
    """Old basic group: negative id without the -100 prefix (no link from the id — only via the Telegram API)."""
    s = str(tg_id or "")
    return s.startswith("-") and not s.startswith("-100") and s[1:].isdigit()


def supergroup_link(tg_id, message_id=None) -> str | None:
    """Supergroup/channel (-100…): Telegram has no "private group by id" link — only a link to a message in it,
    and such a link opens the group itself. Uses the last operation message; with no operations, the first message."""
    s = str(tg_id or "")
    if s.startswith("-100") and s[4:].isdigit():
        return f"https://t.me/c/{s[4:]}/{int(message_id) if message_id else 1}"
    return None


def group_link(chat_type, tg_id, message_id=None, title=None) -> str | None:
    """Link without calling Telegram. Private chat: title holds the username → t.me/<username>
    (tg://user?id= does not open for everyone — fallback only). Old basic group → None
    (its link is fetched by src/utils/group_links.py via the Telegram API)."""
    link = supergroup_link(tg_id, message_id)
    if link:
        return link
    s = str(tg_id or "")
    if s.isdigit() and int(s) > 0:
        name = (title or "").strip().lstrip("@")
        return f"https://t.me/{name}" if _USERNAME.fullmatch(name) else f"tg://user?id={s}"
    return None


def _arrow_html(link: str | None) -> str:
    """↗ is the link; groups without a link get an inactive dot in the same spot (the title column does not shift)."""
    return f'<a href="{escape(link, quote=True)}">{LINK_ARROW}</a>' if link else NO_LINK_MARK


# ---------- flat view ----------

def flat_text(accounts, groups: dict, header: str) -> str:
    """accounts — the page's accounts; groups — {group_id: GroupInfo}.
    Line: <code>amount currency</code> ↗ Title — the title in normal font (narrower than monospace),
    the arrow left of the title, so the arrows form one column."""
    lines = [header]
    if not accounts:
        return header
    amounts = [fmt_amount(a.amount) for a in accounts]
    aw = max(len(x) for x in amounts)
    cw = min(MAX_CURRENCY_PAD, max(len(a.currency or "") for a in accounts))
    for acc, amt in zip(accounts, amounts):
        info = groups.get(acc.group_id)
        label = clip(info.label if info else "?", GROUP_LABEL_MAX)
        code = f"{amt:>{aw}} {clip(acc.currency, cw):<{cw}}".replace(" ", NBSP)
        lines.append(f"<code>{escape(code)}</code> {_arrow_html(info.link if info else None)} {escape(label)}")
    return "\n".join(lines)


def pack_flat(accounts, labels: dict, budget: int = PAGE_TEXT_BUDGET, per_page: int = LINES_PER_PAGE):
    """Flat view: pages of ≤ per_page lines and ≤ budget visible characters.
    Line length is estimated from the widths of the WHOLE list (≥ the widths of any page) — an upper bound,
    so the layout is deterministic. -> [[page accounts], ...]"""
    if not accounts:
        return [[]]
    aw = max(len(fmt_amount(a.amount)) for a in accounts)
    cw = min(MAX_CURRENCY_PAD, max(len(a.currency or "") for a in accounts))
    pages, page, used = [], [], 0
    for acc in accounts:
        ln = aw + 1 + cw + 3 + len(clip(labels.get(acc.group_id, "?"), GROUP_LABEL_MAX)) + 1
        if page and (used + ln > budget or len(page) >= per_page):
            pages.append(page); page, used = [], 0
        page.append(acc); used += ln
    pages.append(page)
    return pages


# ---------- grouped view ----------

def _header_html(info: GroupInfo, continued: bool) -> str:
    parts = [info.emoji, _arrow_html(info.link) if info.link else "", f"<b>{escape(info.label)}</b>"]
    text = " ".join(p for p in parts if p)
    if continued:
        text += CONTINUED
    return text


def _account_html(acc, aw: int) -> str:
    return f"<code>  {fmt_amount(acc.amount):>{aw}} {escape(acc.currency or '')}</code>"


def group_order(accounts, labels: dict):
    """-> [(group_id, [accounts in original order])], groups by title (natural order), then by id."""
    buckets: dict = {}
    for acc in accounts:
        buckets.setdefault(acc.group_id, []).append(acc)
    keys = sorted(buckets, key=lambda k: (_natural_key(labels.get(k, "")), str(k)))
    return [(k, buckets[k]) for k in keys]


def pack_grouped(accounts, labels: dict, budget: int = PAGE_TEXT_BUDGET,
                 per_page: int = LINES_PER_PAGE):
    """Split into pages. -> (pages, aw), where page = [(group_id, [accounts], continued?)].
    The header is measured with room for the emoji and " ↗" (not every group has a link), so the layout
    does not depend on links and the page number is stable between clicks."""
    if not accounts:
        return [[]], 0
    aw = max(len(fmt_amount(a.amount)) for a in accounts)
    pages, page, used, count = [], [], 0, 0

    def head_len(key, continued):
        return visible_len(_header_html(GroupInfo(labels.get(key, ""), "👥", "x"), continued)) + 1

    def line_len(acc):
        return visible_len(_account_html(acc, aw)) + 1

    def flush():
        nonlocal page, used, count
        if page:
            pages.append(page)
        page, used, count = [], 0, 0

    for key, accs in group_order(accounts, labels):
        i, continued = 0, False
        while i < len(accs):
            sep = 1 if page else 0
            if page and (used + sep + head_len(key, continued) + line_len(accs[i]) > budget or count + 1 > per_page):
                flush()
                sep = 0
            used += sep + head_len(key, continued)
            chunk = []
            while i < len(accs):
                ln = line_len(accs[i])
                if chunk and (used + ln > budget or count + 1 > per_page):
                    break
                chunk.append(accs[i]); used += ln; count += 1; i += 1
            page.append((key, chunk, continued))
            if i < len(accs):  # the group did not fit — continue on a new page
                flush()
                continued = True
    flush()
    return pages or [[]], aw


def grouped_text(blocks, groups: dict, aw: int, header: str) -> str:
    parts = [header.rstrip("\n")]
    for n, (key, accs, continued) in enumerate(blocks):
        info = groups.get(key) or GroupInfo("?")
        if n:
            parts.append("")
        parts.append(_header_html(info, continued))
        parts.extend(_account_html(a, aw) for a in accs)
    return "\n".join(parts)
