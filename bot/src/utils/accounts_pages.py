"""Paged "get_all" (admin): all accounts do not fit into one Telegram message (4096-character limit).

State (sort, view, page, filter) is not stored anywhere — it lives in the buttons' callback_data:
  acc_all:<mode>[,<view>]:<page>[:<filter>]   (view: f — flat list, g — by group; filter — space-separated words)
Old buttons without ",<view>" open the flat view.
"""
from .sort_accounts import normalize_sort, CALLBACK_DATA_MAX_BYTES

ALL_CALLBACK_PREFIX = "acc_all:"
ALL_PER_PAGE = 60  # ≤ 2.3k characters on real data; MAX_TEXT_LEN guards the outliers
MAX_TEXT_LEN = 4000  # Telegram limit 4096 minus room for notes

VIEW_FLAT = "f"
VIEW_GROUPS = "g"
VIEWS = (VIEW_FLAT, VIEW_GROUPS)
DEFAULT_VIEW = VIEW_FLAT


def normalize_view(view) -> str:
    return view if view in VIEWS else DEFAULT_VIEW


def toggle_view(view: str) -> str:
    return VIEW_GROUPS if normalize_view(view) == VIEW_FLAT else VIEW_FLAT


def view_label(view: str) -> str:
    """Button label: the view it will switch to."""
    return "👥 By group" if normalize_view(view) == VIEW_FLAT else "📋 As list"


def paginate(items, page: int, per_page: int = ALL_PER_PAGE):
    """-> (page items, page number, total pages). The page is clamped to [1, pages]."""
    pages = max(1, (len(items) + per_page - 1) // per_page)
    page = min(max(1, page), pages)
    start = (page - 1) * per_page
    return items[start:start + per_page], page, pages


def build_all_callback(mode: str, page: int, filter_str: str | None = None, view: str | None = None) -> str | None:
    """None if it does not fit into 64 bytes (long filter)."""
    data = f"{ALL_CALLBACK_PREFIX}{normalize_sort(mode)},{normalize_view(view)}:{int(page)}"
    if filter_str:
        data = f"{data}:{filter_str}"
    return data if len(data.encode("utf-8")) <= CALLBACK_DATA_MAX_BYTES else None


def parse_all_callback(data: str):
    """-> (mode, page, filter|None, view). Garbage → defaults."""
    parts = (data or "")[len(ALL_CALLBACK_PREFIX):].split(":", 2)
    mode_raw, _, view_raw = (parts[0] if parts else "").partition(",")
    mode = normalize_sort(mode_raw)
    view = normalize_view(view_raw)
    try:
        page = int(parts[1]) if len(parts) > 1 else 1
    except ValueError:
        page = 1
    filter_str = parts[2] if len(parts) > 2 and parts[2] else None
    return mode, page, filter_str, view
