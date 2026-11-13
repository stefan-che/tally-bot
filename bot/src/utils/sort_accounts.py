"""Sorting of the account list for "Get" and its toggle button.

Default: by amount. The choice is not stored anywhere — it lives in the button itself (callback_data);
a new "Get" opens sorted by amount again.

Modes:
  name   — by name (A→Z, case-insensitive, "usdt2" < "usdt10"); an account's position does not depend on its balance.
  amount — by balance, largest first; ties broken by name.
"""
import re

SORT_NAME = "name"
SORT_AMOUNT = "amount"
SORT_MODES = (SORT_NAME, SORT_AMOUNT)
DEFAULT_SORT = SORT_AMOUNT

SORT_CALLBACK_PREFIX = "acc_sort:"
CALLBACK_DATA_MAX_BYTES = 64  # Telegram limit for callback_data

_DIGITS = re.compile(r"(\d+)")


def normalize_sort(mode) -> str:
    return mode if mode in SORT_MODES else DEFAULT_SORT


def _natural_key(text: str):
    parts = _DIGITS.split((text or "").casefold())
    return [(0, int(p), "") if p.isdigit() else (1, 0, p) for p in parts if p]


def sort_accounts(accounts, mode: str):
    mode = normalize_sort(mode)
    if mode == SORT_AMOUNT:
        return sorted(accounts, key=lambda a: (-(a.amount or 0), _natural_key(a.currency)))
    return sorted(accounts, key=lambda a: _natural_key(a.currency))


def toggle_target(mode: str) -> str:
    return SORT_AMOUNT if normalize_sort(mode) == SORT_NAME else SORT_NAME


def toggle_label(mode: str) -> str:
    """Button label: the action it will perform."""
    return "💰 Sort by amount" if normalize_sort(mode) == SORT_NAME else "🔤 Sort by name"


def build_sort_callback(target_mode: str, filter_str: str | None = None) -> str | None:
    """acc_sort:<mode>[:<filter>]. None if the filter does not fit into 64 bytes
    (then the button is not shown: silently dropping the filter is worse)."""
    data = SORT_CALLBACK_PREFIX + normalize_sort(target_mode)
    if filter_str:
        data = f"{data}:{filter_str}"
    return data if len(data.encode("utf-8")) <= CALLBACK_DATA_MAX_BYTES else None


def parse_sort_callback(data: str):
    """-> (mode, filter|None). The filter may contain any characters (split is limited)."""
    body = (data or "")[len(SORT_CALLBACK_PREFIX):]
    mode, _, filter_str = body.partition(":")
    return normalize_sort(mode), (filter_str or None)
