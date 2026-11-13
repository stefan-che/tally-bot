"""Tests of the "get_all" pages: python3.11 tests/test_accounts_pages.py"""
import importlib.util, pathlib, sys, types

# load utils directly: the src package pulls in aiogram/colorama
_utils = pathlib.Path(__file__).resolve().parents[1] / "src" / "utils"
pkg = types.ModuleType("u"); pkg.__path__ = [str(_utils)]; sys.modules["u"] = pkg
def _load(name):
    spec = importlib.util.spec_from_file_location(f"u.{name}", _utils / f"{name}.py")
    m = importlib.util.module_from_spec(spec); sys.modules[f"u.{name}"] = m; spec.loader.exec_module(m); return m
_load("sort_accounts"); P = _load("accounts_pages")


def test_paginate_clamps_and_counts():
    items = list(range(85))
    assert P.paginate(items, 1, 40) == (items[:40], 1, 3)
    assert P.paginate(items, 3, 40) == (items[80:], 3, 3)
    assert P.paginate(items, 99, 40)[1:] == (3, 3)
    assert P.paginate(items, -5, 40)[1:] == (1, 3)
    assert P.paginate([], 1, 40) == ([], 1, 1)


def test_callback_roundtrip():
    data = P.build_all_callback("name", 7, "usd eur.x:y")
    assert P.parse_all_callback(data) == ("name", 7, "usd eur.x:y", "f")
    assert P.parse_all_callback(P.build_all_callback("amount", 2)) == ("amount", 2, None, "f")
    assert P.parse_all_callback(P.build_all_callback("name", 3, "usd", "g")) == ("name", 3, "usd", "g")


def test_old_buttons_without_view_open_flat():
    assert P.parse_all_callback("acc_all:name:4:usd") == ("name", 4, "usd", "f")
    assert P.parse_all_callback("acc_all:name,zz:4") == ("name", 4, None, "f")


def test_view_toggle():
    assert P.toggle_view("f") == "g" and P.toggle_view("g") == "f" and P.toggle_view(None) == "g"
    assert "group" in P.view_label("f") and "list" in P.view_label("g")


def test_callback_limit_and_garbage():
    assert P.build_all_callback("name", 1, "é" * 40) is None
    assert P.parse_all_callback("acc_all:zzz:abc") == ("amount", 1, None, "f")
    assert P.parse_all_callback("acc_all:") == ("amount", 1, None, "f")


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("ok", n)
