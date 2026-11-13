"""Paged "/groups" in a private chat (admin): one message with paging, search and filter buttons.

State is not stored anywhere — it lives in the buttons' callback_data (as in "get_all", see accounts_pages.py):
  grp:<status><type><accounts><users><sort><dir>:<page>[:<search>]
    status:   a — all, o — 🟩 Active, i — 🟥 Inactive
    type:     a — all, g — 👥 groups, p — 🧍 private, c — 📢 channels
    accounts: a — all, y — with accounts, n — without accounts
    users:    a — all, y — with users, n — without users
    sort:     n — title, u — users, c — accounts, d — creation date
    dir:      a — ascending ⬆️, d — descending ⬇️ (default: title ⬆️)
Old/malformed data (e.g. 3 flags from the previous version) → missing values fall back to defaults.
The search is trimmed by bytes up front (fit_search) so the buttons always fit into 64 bytes.
"""
from .sort_accounts import CALLBACK_DATA_MAX_BYTES

GROUPS_CALLBACK_PREFIX = "grp:"
GROUPS_PER_PAGE = 10
PAGE_DIGITS_RESERVE = 6  # room for the page number, with a margin (up to 999 999)

ALL = "a"
STATUSES = (ALL, "o", "i")
TYPES = (ALL, "g", "p", "c")
ACCOUNTS = (ALL, "y", "n")
USERS = (ALL, "y", "n")
SORTS = ("n", "u", "c", "d")
DIRS = ("a", "d")
DEFAULT_SORT, DEFAULT_DIR = "n", "a"
FLAGS_LEN = 6

STATUS_LABELS = {ALL: "Status: all", "o": "🟩 Active", "i": "🟥 Inactive"}
TYPE_LABELS = {ALL: "Type: all", "g": "👥 Groups", "p": "🧍 Private", "c": "📢 Channels"}
ACCOUNTS_LABELS = {ALL: "Accounts: all", "y": "💰 With accounts", "n": "🚫 No accounts"}
USERS_LABELS = {ALL: "Users: all", "y": "👤 With users", "n": "🚫 No users"}
SORT_LABELS = {"n": "Sort: title", "u": "Sort: users", "c": "Sort: accounts", "d": "Sort: created"}
DIR_LABELS = {"a": "⬆️ asc", "d": "⬇️ desc"}

# filter codes -> DB values (EGroupStatus / EGroupType); plain strings so the module does not import db
STATUS_VALUES = {"o": "Active", "i": "Inactive"}
TYPE_VALUES = {"g": "GROUP", "p": "PERSONAL", "c": "CHANNEL"}
PRESENCE_VALUES = {"y": True, "n": False}  # accounts/users: None — no filter
SORT_FIELDS = {"n": "name", "u": "users", "c": "accounts", "d": "created"}

# max bytes for the search: prefix + flags + ":" + page + ":"
SEARCH_MAX_BYTES = CALLBACK_DATA_MAX_BYTES - len(GROUPS_CALLBACK_PREFIX) - FLAGS_LEN - 1 - PAGE_DIGITS_RESERVE - 1


def _norm(value, allowed, default=ALL) -> str:
    return value if value in allowed else default


def normalize_filters(status=None, chat_type=None, accounts=None, users=None, sort=None, direction=None):
    """-> (status, chat_type, accounts, users, sort, direction); anything not in the allowed list → default."""
    return (_norm(status, STATUSES), _norm(chat_type, TYPES), _norm(accounts, ACCOUNTS), _norm(users, USERS),
            _norm(sort, SORTS, DEFAULT_SORT), _norm(direction, DIRS, DEFAULT_DIR))


def cycle(value, allowed) -> str:
    """Next value in the cycle (toggle button). Garbage → first value, then one step."""
    value = _norm(value, allowed, allowed[0])
    return allowed[(allowed.index(value) + 1) % len(allowed)]


def fit_search(search: str | None, max_bytes: int = SEARCH_MAX_BYTES) -> str | None:
    """Trim the search to UTF-8 bytes without splitting a character. ':' inside the search is fine (the search is the data tail)."""
    search = (search or "").strip()
    if not search:
        return None
    cut = search.encode("utf-8")[:max_bytes].decode("utf-8", errors="ignore").strip()
    return cut or None


def clamp_page(page, total: int, per_page: int = GROUPS_PER_PAGE):
    """-> (page, total pages, offset). The page is clamped to [1, pages]."""
    try:
        page = int(page)
    except (TypeError, ValueError):
        page = 1
    pages = max(1, (max(0, total) + per_page - 1) // per_page)
    page = min(max(1, page), pages)
    return page, pages, (page - 1) * per_page


def build_groups_callback(page: int, status=None, chat_type=None, accounts=None, search: str | None = None,
                          users=None, sort=None, direction=None) -> str | None:
    """None if it does not fit into 64 bytes (the search did not go through fit_search)."""
    flags = "".join(normalize_filters(status, chat_type, accounts, users, sort, direction))
    data = f"{GROUPS_CALLBACK_PREFIX}{flags}:{int(page)}"
    if search:
        data = f"{data}:{search}"
    return data if len(data.encode("utf-8")) <= CALLBACK_DATA_MAX_BYTES else None


def parse_groups_callback(data: str):
    """-> (page, status, chat_type, accounts, search|None, users, sort, direction). Garbage → defaults."""
    parts = (data or "")[len(GROUPS_CALLBACK_PREFIX):].split(":", 2)
    flags = parts[0] if parts else ""
    s, t, a, u, srt, d = normalize_filters(*(flags[i:i + 1] for i in range(FLAGS_LEN)))
    try:
        page = int(parts[1]) if len(parts) > 1 else 1
    except ValueError:
        page = 1
    search = parts[2] if len(parts) > 2 and parts[2] else None
    return page, s, t, a, search, u, srt, d


def is_groups_callback(data: str | None) -> bool:
    return bool(data) and data.startswith(GROUPS_CALLBACK_PREFIX)
