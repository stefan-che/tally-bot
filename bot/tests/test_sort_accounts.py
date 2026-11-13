"""Tests of the "Get" sorting: python3.11 -m pytest tests/ (or python3.11 tests/test_sort_accounts.py)."""
import importlib.util, pathlib
from types import SimpleNamespace as Acc

# load the module directly: the src package pulls in aiogram/colorama, the utility itself is pure
_path = pathlib.Path(__file__).resolve().parents[1] / "src" / "utils" / "sort_accounts.py"
_spec = importlib.util.spec_from_file_location("sort_accounts", _path)
_m = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_m)
sort_accounts, build_sort_callback, parse_sort_callback = _m.sort_accounts, _m.build_sort_callback, _m.parse_sort_callback
toggle_target, toggle_label, normalize_sort = _m.toggle_target, _m.toggle_label, _m.normalize_sort
SORT_NAME, SORT_AMOUNT, CALLBACK_DATA_MAX_BYTES = _m.SORT_NAME, _m.SORT_AMOUNT, _m.CALLBACK_DATA_MAX_BYTES


def names(accs):
    return [a.currency for a in accs]


def test_name_mode_ignores_balance():
    before = [Acc(currency="usd", amount=0), Acc(currency="eur", amount=0), Acc(currency="rub", amount=0)]
    after = [Acc(currency="usd", amount=-200), Acc(currency="eur", amount=0), Acc(currency="rub", amount=1500)]
    assert names(sort_accounts(before, SORT_NAME)) == names(sort_accounts(after, SORT_NAME)) == ["eur", "rub", "usd"]


def test_name_mode_case_insensitive_and_natural():
    accs = [Acc(currency=c, amount=0) for c in ["usdt10", "USD", "usdt2", "Éuro", "aed"]]
    assert names(sort_accounts(accs, SORT_NAME)) == ["aed", "USD", "usdt2", "usdt10", "Éuro"]


def test_amount_mode_desc_with_name_tiebreak():
    accs = [Acc(currency="usd", amount=0), Acc(currency="rub", amount=5), Acc(currency="eur", amount=0), Acc(currency="aed", amount=-1)]
    assert names(sort_accounts(accs, SORT_AMOUNT)) == ["rub", "eur", "usd", "aed"]


def test_default_and_unknown_mode_is_amount():
    assert normalize_sort(None) == SORT_AMOUNT
    assert normalize_sort("bogus") == SORT_AMOUNT


def test_toggle():
    assert toggle_target(SORT_NAME) == SORT_AMOUNT and toggle_target(SORT_AMOUNT) == SORT_NAME
    assert "amount" in toggle_label(SORT_NAME) and "name" in toggle_label(SORT_AMOUNT)


def test_callback_roundtrip_with_filter_containing_separators():
    data = build_sort_callback(SORT_AMOUNT, "usd.t:x-éü")
    assert parse_sort_callback(data) == (SORT_AMOUNT, "usd.t:x-éü")


def test_callback_never_exceeds_limit():
    assert build_sort_callback(SORT_NAME, "é" * 40) is None  # does not fit → no button, the filter is not dropped silently
    data = build_sort_callback(SORT_NAME, "é" * 20)
    assert len(data.encode()) <= CALLBACK_DATA_MAX_BYTES and parse_sort_callback(data) == (SORT_NAME, "é" * 20)


def test_forged_callback_is_harmless():
    assert parse_sort_callback("acc_sort:DROP TABLE") == (SORT_AMOUNT, None)
    assert parse_sort_callback("acc_sort:") == (SORT_AMOUNT, None)


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("ok", n)
