"""Tests of the "get_all" layout (flat / by group): python3.11 tests/test_accounts_layout.py"""
import importlib.util, pathlib, re, sys, types
from types import SimpleNamespace as NS

_utils = pathlib.Path(__file__).resolve().parents[1] / "src" / "utils"
pkg = types.ModuleType("u"); pkg.__path__ = [str(_utils)]; sys.modules["u"] = pkg
def _load(name):
    spec = importlib.util.spec_from_file_location(f"u.{name}", _utils / f"{name}.py")
    m = importlib.util.module_from_spec(spec); sys.modules[f"u.{name}"] = m; spec.loader.exec_module(m); return m
_load("sort_accounts"); L = _load("accounts_layout")


def acc(cur, amount, gid):
    return NS(currency=cur, amount=amount, group_id=gid)


def plain(html):
    return re.sub(r"<[^>]+>", "", html).replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")


def test_group_link():
    assert L.group_link("GROUP", -1001234567890, 55) == "https://t.me/c/1234567890/55"
    assert L.group_link("GROUP", -1001234567890, None) == "https://t.me/c/1234567890/1"  # no operations — first message
    assert L.group_link("GROUP", -123456, 55) is None              # old basic group — no link
    assert L.group_link("PERSONAL", 777, None, "user_k") == "https://t.me/user_k"   # private chat — by username
    assert L.group_link("PERSONAL", 777, None, "@User_K") == "https://t.me/User_K"
    assert L.group_link("PERSONAL", 777, None, "N/A") == "tg://user?id=777"         # no username — fallback
    assert L.group_link("GROUP", 777, None) == "tg://user?id=777"  # private chat with a wrong chat_type in the DB
    assert L.group_link("PERSONAL", 777, None, 'x"><script>') == "tg://user?id=777"
    assert L.is_basic_group_id(-123456) and not L.is_basic_group_id(-1001234567890) and not L.is_basic_group_id(777)
    assert L.group_link("GROUP", None, 1) is None


def test_label_and_clip():
    assert L.group_label(None, -100) == "-100" and L.group_label("  ", 5) == "5"
    assert L.clip("Northern Exchange", 8) == "Norther…" and L.clip("abc", 8) == "abc"


def test_flat_arrow_left_of_plain_group_name():
    g = {1: L.GroupInfo("Northern branch main desk", link="https://t.me/c/1/2"), 2: L.GroupInfo("Cashbox")}
    text = L.flat_text([acc("usdt", 125000, 1), acc("kzt", -150, 2), acc("rub", 0, 1)], g, "H")
    rows = text.split("\n")[1:]
    nb = L.NBSP
    assert rows[0].startswith(f"<code>125’000{nb}usdt</code> ") and " " not in re.search(r"<code>(.*?)</code>", rows[1]).group(1)
    assert '</code> <a href="https://t.me/c/1/2">↗</a> Northern' in rows[0]   # arrow on the left, title outside <code>
    assert rows[1].endswith("</code> · Cashbox")                                # no link — a dot in place of the arrow
    codes = [re.search(r"<code>(.*?)</code>", r).group(1) for r in rows]
    assert len({len(c) for c in codes}) == 1                                    # code part has one width → arrows in one column
    assert len({c.index(x) + len(x) for c, x in zip(codes, ["125’000", "-150", "0"])}) == 1  # amounts right-aligned
    assert plain(rows[0]).endswith("…") and len(plain(rows[0]).split("↗ ")[1]) == L.GROUP_LABEL_MAX
    long = L.flat_text([acc("u" * 24, 1, 1), acc("usd", 2, 1)], g, "H").split("\n")[1:]
    assert len({len(re.search(r"<code>(.*?)</code>", r).group(1)) for r in long}) == 1   # a long currency does not break the column


def test_pack_flat_budget_and_count():
    accs = [acc("usdt", 1, 1) for _ in range(300)]
    pages = L.pack_flat(accs, {1: "Cashbox"})
    assert [len(p) for p in pages] == [30] * 10
    big = [acc("x" * 24, 10 ** 12, 1) for _ in range(300)]
    pages = L.pack_flat(big, {1: "W" * 40})
    infos = {1: L.GroupInfo("W" * 40, link="https://t.me/c/1/2")}
    assert all(L.visible_len(L.flat_text(p, infos, "H" * 60)) <= 4000 for p in pages)
    assert sum(map(len, pages)) == 300 and L.pack_flat([], {}) == [[]]


def test_visible_len_ignores_tags_and_hrefs():
    assert L.visible_len('<code>a&amp;b</code> <a href="https://t.me/c/1/2">↗</a>') == 5


def test_flat_escapes_html():
    text = L.flat_text([acc("<b>", 1, 1)], {1: L.GroupInfo("<script>")}, "H")
    assert "<script>" not in text and "&lt;b&gt;" in text


def test_grouped_order_headers_links_escape():
    accs = [acc("usd", 5, "b"), acc("usdt", 9, "a"), acc("rub", 1, "b")]
    labels = {"a": "Apple", "b": "<Alpha>"}
    pages, aw = L.pack_grouped(accs, labels)
    assert len(pages) == 1 and [k for k, _, _ in pages[0]] == ["b", "a"]  # groups ordered by title
    infos = {"b": L.GroupInfo("<Alpha>", "👥", "https://t.me/c/1/2"), "a": L.GroupInfo("Apple", "🧍")}
    text = L.grouped_text(pages[0], infos, aw, "H\n")
    assert "&lt;Alpha&gt;" in text and '<a href="https://t.me/c/1/2">↗</a>' in text
    lines = text.split("\n")
    assert lines[1] == '👥 <a href="https://t.me/c/1/2">↗</a> <b>&lt;Alpha&gt;</b>'  # arrow left of the title
    assert lines[1].startswith("👥") and "usd" in lines[2] and "rub" in lines[3] and lines[4] == ""


def test_grouped_split_long_group_marks_continuation():
    accs = [acc(f"c{i}", i, "a") for i in range(70)] + [acc("x", 1, "b")]
    pages, aw = L.pack_grouped(accs, {"a": "A", "b": "B"})
    assert len(pages) == 3
    assert pages[0][0][2] is False and pages[1][0][2] is True and len(pages[0][0][1]) == 30
    assert sum(len(c) for p in pages for _, c, _ in p) == 71
    infos = {"a": L.GroupInfo("A", "👥", "https://t.me/c/1234567890123/9999999"), "b": L.GroupInfo("B")}
    for p in pages:
        assert len(L.grouped_text(p, infos, aw, "H\n")) < 4000
    assert "(cont.)" in L.grouped_text(pages[1], infos, aw, "H\n")


def test_grouped_text_budget_worst_case():
    accs = [acc("&" * 32, 10 ** 12, i) for i in range(200)]
    labels = {i: "&" * 32 for i in range(200)}
    pages, aw = L.pack_grouped(accs, labels)
    infos = {i: L.GroupInfo("&" * 32, "👥", "https://t.me/c/1234567890123/9999999999") for i in range(200)}
    header = "<code>Funds by group: page 99/99 · groups 999 · accounts 9999</code>\n"
    for p in pages:
        assert L.visible_len(L.grouped_text(p, infos, aw, header)) <= 4000


def test_empty():
    assert L.pack_grouped([], {}) == ([[]], 0)
    assert L.flat_text([], {}, "H") == "H"


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("ok", n)
