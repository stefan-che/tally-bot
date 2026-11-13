"""Tests of the /groups pages in a private chat: python3.11 tests/test_groups_pages.py"""
import importlib.util, pathlib, sys, types

# load utils directly: the src package pulls in aiogram/colorama
_utils = pathlib.Path(__file__).resolve().parents[1] / "src" / "utils"
pkg = types.ModuleType("u"); pkg.__path__ = [str(_utils)]; sys.modules["u"] = pkg
def _load(name):
    spec = importlib.util.spec_from_file_location(f"u.{name}", _utils / f"{name}.py")
    m = importlib.util.module_from_spec(spec); sys.modules[f"u.{name}"] = m; spec.loader.exec_module(m); return m
_load("sort_accounts"); G = _load("groups_pages")


D = ("a", "a", "a", "a", "n", "a")  # status, type, accounts, users, sort, dir — defaults


def P(page, s="a", t="a", a="a", search=None, u="a", srt="n", d="a"):
    return (page, s, t, a, search, u, srt, d)


def test_callback_roundtrip():
    assert G.parse_groups_callback(G.build_groups_callback(1)) == P(1)
    assert G.build_groups_callback(1) == "grp:aaaana:1"
    data = G.build_groups_callback(7, "o", "p", "y", "chät: x.y")
    assert data == "grp:opyana:7:chät: x.y"
    assert G.parse_groups_callback(data) == P(7, "o", "p", "y", "chät: x.y")
    data = G.build_groups_callback(2, "i", "c", "n", "-100123", users="y", sort="d", direction="d")
    assert data == "grp:icnydd:2:-100123"
    assert G.parse_groups_callback(data) == P(2, "i", "c", "n", "-100123", "y", "d", "d")
    for srt in G.SORTS:
        for d in G.DIRS:
            for u in G.USERS:
                cb = G.build_groups_callback(3, users=u, sort=srt, direction=d)
                assert G.parse_groups_callback(cb) == P(3, u=u, srt=srt, d=d)


def test_garbage_falls_back_to_defaults():
    assert G.parse_groups_callback("grp:") == P(1)
    assert G.parse_groups_callback("grp:zzz:abc") == P(1)
    assert G.parse_groups_callback("grp:zzzzzzzz:3") == P(3)
    assert G.parse_groups_callback(None) == P(1)
    assert G.build_groups_callback(1, "x", "y", "z", users="q", sort="q", direction="q") == "grp:aaaana:1"
    # old button (3 flags) — new fields get defaults, the search is kept
    assert G.parse_groups_callback("grp:opy:7:chät") == P(7, "o", "p", "y", "chät")
    assert G.is_groups_callback("grp:aaa:1") and not G.is_groups_callback("acc_all:x") and not G.is_groups_callback(None)


def test_byte_limit():
    assert G.SEARCH_MAX_BYTES == 64 - 4 - 6 - 1 - 6 - 1
    long = "é" * 40  # 80 bytes
    assert G.build_groups_callback(1, search=long) is None
    fitted = G.fit_search(long)
    assert len(fitted.encode("utf-8")) <= G.SEARCH_MAX_BYTES
    assert fitted == "é" * (G.SEARCH_MAX_BYTES // 2)  # no character is split
    for page in (1, 999999):  # the button fits with any page number and any filters
        for srt in G.SORTS:
            data = G.build_groups_callback(page, "i", "c", "n", fitted, users="n", sort=srt, direction="d")
            assert data and len(data.encode("utf-8")) <= 64
            assert G.parse_groups_callback(data)[4] == fitted
    worst = G.fit_search("😀" * 30)  # 4-byte characters
    data = G.build_groups_callback(999999, "i", "c", "y", worst, users="y", sort="d", direction="d")
    assert data and len(data.encode("utf-8")) <= 64
    assert G.fit_search("  abc  ") == "abc"
    assert G.fit_search("   ") is None and G.fit_search(None) is None
    assert G.fit_search("ab😀", max_bytes=4) == "ab"  # a 4-byte emoji is not cut in half


def test_filter_cycling():
    assert [G.cycle(s, G.STATUSES) for s in ("a", "o", "i")] == ["o", "i", "a"]
    assert [G.cycle(t, G.TYPES) for t in ("a", "g", "p", "c")] == ["g", "p", "c", "a"]
    assert [G.cycle(a, G.ACCOUNTS) for a in ("a", "y", "n")] == ["y", "n", "a"]
    assert [G.cycle(u, G.USERS) for u in ("a", "y", "n")] == ["y", "n", "a"]
    assert [G.cycle(s, G.SORTS) for s in ("n", "u", "c", "d")] == ["u", "c", "d", "n"]
    assert [G.cycle(d, G.DIRS) for d in ("a", "d")] == ["d", "a"]
    assert G.cycle("junk", G.TYPES) == "g" and G.cycle("junk", G.SORTS) == "u"
    for codes, labels in ((G.STATUSES, G.STATUS_LABELS), (G.TYPES, G.TYPE_LABELS), (G.ACCOUNTS, G.ACCOUNTS_LABELS),
                          (G.USERS, G.USERS_LABELS), (G.SORTS, G.SORT_LABELS), (G.DIRS, G.DIR_LABELS)):
        assert set(codes) == set(labels)
    assert set(G.STATUS_VALUES) == set(G.STATUSES) - {"a"} and set(G.TYPE_VALUES) == set(G.TYPES) - {"a"}
    assert set(G.PRESENCE_VALUES) == set(G.ACCOUNTS) - {"a"} == set(G.USERS) - {"a"}
    assert set(G.SORT_FIELDS) == set(G.SORTS)
    assert G.normalize_filters() == D


def test_page_clamp():
    assert G.clamp_page(1, 0) == (1, 1, 0)
    assert G.clamp_page(5, 0) == (1, 1, 0)
    assert G.clamp_page(2, 25, 10) == (2, 3, 10)
    assert G.clamp_page(99, 25, 10) == (3, 3, 20)
    assert G.clamp_page(-3, 25, 10) == (1, 3, 0)
    assert G.clamp_page("x", 25, 10) == (1, 3, 0)
    assert G.clamp_page(2, 20, 10) == (2, 2, 10)


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("ok", n)
