#!/usr/bin/env python3
"""Turn a structured Markdown research report into a Guige-style single HTML page.

Usage:
  python3 build.py REPORT.md -o OUT_DIR [--meta meta.yaml] [--hero hero.png] [--no-embed-hero]

Requires: pandoc (system), python packages: beautifulsoup4, pyyaml (Pillow optional, for hero -> webp).
See README.md for the expected Markdown skeleton and meta.yaml fields.
"""
import argparse, base64, shutil, datetime as dt, html, io, json, math, os, re, subprocess, sys
from collections import Counter
from urllib.parse import urlparse
import yaml
from bs4 import BeautifulSoup, NavigableString

HERE = os.path.dirname(os.path.abspath(__file__))
MERMAID_URL = "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs"

# Bracketed evidence markers -> badge class. First matching keyword wins. Text is kept verbatim.
DEFAULT_MARKERS = [
    ("待核实", "verify"), ("未核实", "verify"), ("未经官方确认", "verify"),
    ("二手", "second"), ("用户探测", "second"), ("非官方", "second"), ("推断", "infer"),
    ("以官网为准", "note"), ("以官方文本为准", "note"), ("口径", "note"), ("信源为", "note"),
    ("已核实", "ok"), ("厂商自报", "self"),
]
MARKER_LABEL = {"verify": "待核实/未核实", "second": "二手/非官方", "infer": "推断",
                "note": "口径/以官方为准", "ok": "已核实", "self": "厂商自报"}
# Bold verification verdicts such as **已核实（官方文档）** / **部分核实（媒体报道）** (no brackets) -> ok badge
VERDICT_RE = re.compile(r"^(已核实|部分核实)(（[^（）]{0,20}）)?$")
TAG_COLORS = ["tag-teal", "tag-amber", "tag-purple"]
WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def split_front_matter(text):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        return {}, text
    return (yaml.safe_load(m.group(1)) or {}), text[m.end():]


def pandoc(md, shift=1):
    exe = os.environ.get("PANDOC") or shutil.which("pandoc") or "/workspace/tools/pandoc"
    r = subprocess.run([exe, "-f", "gfm-tex_math_dollars-tex_math_gfm", "-t", "html5", "--wrap=none", f"--shift-heading-level-by={shift}"],
                       input=md.encode(), capture_output=True, check=True)
    out = r.stdout.decode()
    if "\ufe0e" not in md:          # pandoc adds U+FE0E after some symbols (e.g. ↔); keep the text verbatim
        out = out.replace("\ufe0e", "")
    return out


def text_len_minutes(text):
    cjk = len(re.findall(r"[\u3400-\u9fff]", text))
    words = len(re.findall(r"[A-Za-z0-9_]+", text))
    return max(1, math.ceil(cjk / 500 + words / 220))


def secno_and_rest(title):
    m = re.match(r"^\s*(\d+(?:\.\d+)*|[A-Z](?:\.\d+)*)\.?\s+(.*)$", title)
    return (m.group(1), m.group(2)) if m else (None, title)


def sanitize_mermaid(src):
    """Presentation-only fix: quote node labels that contain characters mermaid's parser rejects
    (parentheses etc.) without changing the visible text."""
    def q(m):
        ident, o, label, c = m.group(1), m.group(2), m.group(3), m.group(4)
        if label.startswith('"') or not re.search(r"[(){}]", label):
            return m.group(0)
        return f'{ident}{o}"{label.replace(chr(34), "#quot;")}"{c}'
    # A[...], B[(...)] style shapes: only handle plain [..] here
    src = re.sub(r"\b([A-Za-z][\w-]*)(\[)(?!\()([^\[\]\"]*?)(\])", q, src)
    # edge labels |...| containing parens
    src = re.sub(r"\|([^|\"\n]*[(){}][^|\"\n]*)\|", lambda m: '|"' + m.group(1) + '"|', src)
    return src


DEFAULT_UPDATE_PATTERNS = [r"^（?(更新|更正)", r"官方否认"]


def mark_update_notes(soup, patterns):
    """Correction / denial notes (e.g. **（更新：…官方否认…）**) -> visible callout. Text kept verbatim."""
    rx = [re.compile(p) for p in patterns]
    n = 0
    for st in soup.find_all(["strong", "b"]):
        t = st.get_text().strip()
        if len(t) > 4 and any(r.search(t) for r in rx):
            st["class"] = st.get("class", []) + ["upd-note"]; n += 1
    # plain-text parentheticals such as （此后已被官方否认，见 F 节）
    prx = re.compile(r"（[^（）]{0,40}官方否认[^（）]{0,40}）|[^。；，、（）\s][^。；（）]{0,30}官方否认[^。；（）]{0,20}[。；]?")
    for node in list(soup.find_all(string=prx)):
        if node.find_parent(["pre", "code", "script", "style"]) or node.find_parent(class_="upd-note") \
                or node.parent.name in ("strong", "b", "a") or node.find_parent("figure"):
            continue
        s_, parts, last = str(node), [], 0
        for m in prx.finditer(s_):
            parts.append(NavigableString(s_[last:m.start()]))
            sp = soup.new_tag("span", attrs={"class": "upd-note"}); sp.string = m.group(0)
            parts.append(sp); last = m.end(); n += 1
        parts.append(NavigableString(s_[last:]))
        for p_ in parts:
            node.insert_before(p_)
        node.extract()
    return n


YEAR_RE = re.compile(r"^\s*(19|20)\d{2}")
NUM_RE = re.compile(r"^[~≈约<>≥≤+−\-]?\s*[$¥]?\d[\d,.]*\s*(%|K|M|T|B|万|亿)?(\s*(tok/s|/s))?"
                    r"(\s*[/／]\s*([$¥]?\d[\d,.]*|【[^】]*】)\s*(%|K|M|T)?)*")


def convert_timelines(soup):
    """Tables shaped like timelines -> timeline cards. Cell HTML is moved verbatim (no text added
    except the column headers, which are repeated as year/time labels).
      vendor kind: header = 厂商 | 2023 | 2024 | ...   -> one card per row (vendor), one node per year
      stage kind:  header = 阶段 | 时间 | ...           -> vertical stage timeline"""
    n_v = n_s = 0
    for tb in list(soup.find_all("table")):
        ths = [th.get_text().strip() for th in tb.select("thead th")]
        rows = tb.select("tbody tr")
        if len(ths) < 3 or not rows:
            continue
        if ths[0] in ("厂商", "公司", "厂商/机构") and all(YEAR_RE.match(t) for t in ths[1:]):
            grid = soup.new_tag("div", attrs={"class": "tl-grid"})
            for tr in rows:
                tds = tr.find_all("td")
                card = soup.new_tag("article", attrs={"class": "tl-card"})
                hd = soup.new_tag("div", attrs={"class": "tl-vendor"})
                for c in list(tds[0].contents): hd.append(c.extract())
                card.append(hd)
                ol = soup.new_tag("ol", attrs={"class": "tl-track"})
                for i, td in enumerate(tds[1:], 1):
                    empty = td.get_text().strip() in ("", "—", "-")
                    li = soup.new_tag("li", attrs={"class": "tl-node" + (" tl-now" if i == len(tds) - 1 else "") + (" tl-empty" if empty else "")})
                    y = soup.new_tag("span", attrs={"class": "tl-year"}); y.string = ths[i] if i < len(ths) else ""
                    body = soup.new_tag("div", attrs={"class": "tl-body"})
                    for c in list(td.contents): body.append(c.extract())
                    li.append(y); li.append(body); ol.append(li)
                card.append(ol); grid.append(card); n_v += 1
            tb.replace_with(grid)
        elif ths[0] == "阶段" and ths[1] == "时间":
            ol = soup.new_tag("ol", attrs={"class": "stage-tl"})
            for tr in rows:
                tds = tr.find_all("td")
                li = soup.new_tag("li", attrs={"class": "stage"})
                top = soup.new_tag("div", attrs={"class": "stage-top"})
                nm = soup.new_tag("span", attrs={"class": "stage-name"})
                for c in list(tds[0].contents): nm.append(c.extract())
                tm = soup.new_tag("span", attrs={"class": "stage-time"})
                for c in list(tds[1].contents): tm.append(c.extract())
                top.append(tm); top.append(nm); li.append(top)
                for j, td in enumerate(tds[2:], 2):
                    row = soup.new_tag("div", attrs={"class": "stage-row"})
                    lab = soup.new_tag("span", attrs={"class": "stage-lab"}); lab.string = ths[j] if j < len(ths) else ""
                    val = soup.new_tag("div", attrs={"class": "stage-val"})
                    for c in list(td.contents): val.append(c.extract())
                    row.append(lab); row.append(val); li.append(row)
                ol.append(li); n_s += 1
            tb.replace_with(ol)
    return n_v, n_s


def enhance_table(soup, tb, long_rows=12):
    """Numeric columns -> right-aligned tabular figures; long tables get a capped-height box so the
    sticky header works; wide tables get a sticky first column."""
    rows = tb.select("tbody tr")
    ncol = max((len(r.find_all(["td", "th"])) for r in rows), default=0)
    for ci in range(1, ncol):
        cells = [r.find_all(["td", "th"])[ci] for r in rows if len(r.find_all(["td", "th"])) > ci]
        vals = [c.get_text().strip() for c in cells]
        real = [v for v in vals if v not in ("", "—", "-", "–")]
        if not real:
            continue
        good = [v for v in real if NUM_RE.match(v) and len(v) <= 40 and not re.search(r"[\u4e00-\u9fff]{3,}", v)]
        if len(good) / len(real) >= 0.6:
            for c in cells:
                c["class"] = c.get("class", []) + ["num"]
            ths = tb.select("thead th")
            if ci < len(ths):
                ths[ci]["class"] = ths[ci].get("class", []) + ["num"]
    cls = ["table-scroll"]
    first_th = (tb.select_one("thead th").get_text().strip() if tb.select_one("thead th") else "")
    # field/spec tables (header 字段 | model A | model B …) read top-to-bottom: never cap their height
    if len(rows) > long_rows and first_th not in ("字段", "项目", "维度"): cls.append("tall")
    if ncol >= 5: cls.append("wide")
    firsts = [r.find(["td", "th"]).get_text().strip() for r in rows if r.find(["td", "th"])]
    if firsts and max(len(f) for f in firsts) <= 24: cls.append("fc-nw")
    return cls



# Product-card field blocks: a top-level list whose items start with **Label**： becomes labelled
# sub-blocks. First matching key wins; the label text itself is kept verbatim.
DEFAULT_CARD_BLOCKS = [("当前状态", "status"), ("状态", "status"), ("背景", "status"), ("迭代路线", "roadmap"),
                       ("定位与特点", "position"), ("核心定位", "position"), ("主要特点", "feature"),
                       ("技术实现", "tech"), ("商业模式", "biz"), ("局限", "limit"), ("来源", "source")]
GROUP_RE = re.compile(r"^\s*(已发布|已宣布|宣布中)([^：:]{0,20})[：:]\s*")
DATE_RE = re.compile(r"^\s*((?:\d{4}-)?\d{2}-\d{2}(?:/\d{2})?|\d{4}-\d{2}|\d{1,2}\s?月(?:底|初|中旬)?|[A-Z][A-Za-z]+(?: [A-Z][A-Za-z]+)?(?=：))(\s*起)?\s*[：:]?\s*")


def _first_text(node):
    for c in node.descendants:
        if isinstance(c, NavigableString):
            if c.strip():
                return c
            continue
    return None


def _strip_prefix(node, rx):
    """Remove a regex-matched prefix from the first non-empty text node of `node`; return the match."""
    t = _first_text(node)
    if t is None:
        return None
    m = rx.match(str(t))
    if not m:
        return None
    t.replace_with(NavigableString(str(t)[m.end():]))
    return m


def build_roadmap(soup, ul):
    """Roadmap list -> mini timeline. Group items (已发布 / 已宣布 / 宣布中) become headers; a leading date
    (09-08 / 2026-04 起 / 03 月 / Meta Connect) becomes the node's date chip. All other text is moved verbatim."""
    ol = soup.new_tag("ol", attrs={"class": "mtl"})
    n = 0

    def add_node(contents, future):
        nonlocal n
        li = soup.new_tag("li", attrs={"class": "mtl-node" + (" mtl-future" if future else "")})
        body = soup.new_tag("div", attrs={"class": "mtl-body"})
        for c in contents:
            body.append(c.extract() if hasattr(c, "extract") else c)
        m = _strip_prefix(body, DATE_RE)
        if m:
            d = soup.new_tag("span", attrs={"class": "mtl-date"}); d.string = (m.group(1) + (m.group(2) or "")).strip()
            li.append(d)
        li.append(body); ol.append(li); n += 1

    for li in ul.find_all("li", recursive=False):
        sub = li.find(["ul", "ol"], recursive=False)
        if sub is not None: sub.extract()
        m = _strip_prefix(li, GROUP_RE)
        if m:
            future = m.group(1) != "已发布"
            hd = soup.new_tag("li", attrs={"class": "mtl-head" + (" mtl-future" if future else "")})
            hd.string = (m.group(1) + m.group(2)).strip()
            ol.append(hd)
            rest = [c for c in list(li.contents)]
            if "".join(c.get_text() if hasattr(c, "get_text") else str(c) for c in rest).strip():
                add_node(rest, future)
            if sub is not None:
                for s_ in sub.find_all("li", recursive=False):
                    add_node(list(s_.contents), future)
        else:
            add_node(list(li.contents), False)
            if sub is not None:                       # keep any nested detail under the node
                ol.contents[-1].find("div", class_="mtl-body").append(sub)
    ul.replace_with(ol)
    return n


def enhance_cards(soup, blocks):
    n_blk = n_rm = 0
    for card in soup.select("section.p-card"):
        for ul in card.find_all("ul", recursive=False):
            items = ul.find_all("li", recursive=False)
            labelled = []
            for li in items:
                first = next((c for c in li.contents if not (isinstance(c, NavigableString) and not c.strip())), None)
                lab = first.get_text().strip() if getattr(first, "name", None) == "strong" else ""
                cat = next((c for k, c in blocks if lab.startswith(k)), None) if lab else None
                labelled.append((li, first, cat))
            if not items or sum(1 for _, _, c in labelled if c) < max(2, len(items) * 0.6):
                continue
            grid = soup.new_tag("div", attrs={"class": "cblks"})
            for li, first, cat in labelled:
                blk = soup.new_tag("div", attrs={"class": f"cblk cblk-{cat or 'other'}"})
                hd = soup.new_tag("div", attrs={"class": "cblk-h"})
                body = soup.new_tag("div", attrs={"class": "cblk-b"})
                if cat:
                    hd.append(first.extract())
                    nxt = li.contents[0] if li.contents else None
                    if isinstance(nxt, NavigableString):
                        m = re.match(r"^(（[^（）]{0,40}）)?\s*[：:]\s*", str(nxt))
                        if m:
                            if m.group(1):
                                q = soup.new_tag("span", attrs={"class": "cblk-q"}); q.string = m.group(1); hd.append(q)
                            nxt.replace_with(NavigableString(str(nxt)[m.end():]))
                for c in list(li.contents):
                    body.append(c.extract())
                if cat == "roadmap":
                    sub = body.find(["ul", "ol"], recursive=False)
                    if sub is not None:
                        n_rm += 1; build_roadmap(soup, sub)
                if cat: blk.append(hd)
                blk.append(body); grid.append(blk); n_blk += 1
            kids = grid.find_all("div", class_="cblk", recursive=False)   # side-by-side only for a 定位+特点 pair
            for x, y in zip(kids, kids[1:]):
                if "cblk-position" in x["class"] and "cblk-feature" in y["class"]:
                    x["class"].append("cblk-half"); y["class"].append("cblk-half")
            ul.replace_with(grid)
    return n_blk, n_rm


def mark_update_blocks(soup, labels):
    """**状态更正**： paragraph + the list right after it -> one visible correction callout box."""
    n = 0
    for p in soup.find_all("p"):
        st = p.find("strong")
        if not st or p.contents[0] is not st and str(p.contents[0]).strip():
            continue
        if st.get_text().strip() in labels and re.fullmatch(r"\s*[：:]?\s*", p.get_text()[len(st.get_text()):]):
            box = soup.new_tag("div", attrs={"class": "upd-block"})
            p.insert_before(box)
            nxt = p.find_next_sibling()
            box.append(p.extract())
            if nxt is not None and nxt.name in ("ul", "ol"):
                box.append(nxt.extract())
            n += 1
    return n



def _norm_name(x):
    # name tokens; 2-char Latin tokens such as "AI" are too generic to identify a product
    return [t for t in re.split(r"[\s/（）()、，,·]+", x) if len(t) >= 3 or (len(t) == 2 and re.search(r"[\u4e00-\u9fff]", t))]


def tag_table_rows(soup, specs):
    """row_tags: [{header, rules:[[prefix, cls, label?]], filter?}] — rows whose cell under `header` starts with
    `prefix` get tr.row-<cls> and td.rt-<cls>. Tables without that column can inherit the tag from the first
    column by unambiguous product-name match ({inherit: true}); unmatched or ambiguous rows stay untagged."""
    name_map, n_tag, n_inh, filters = {}, 0, 0, 0
    tables = soup.find_all("table")
    for spec in specs:
        for tb in tables:
            ths = [th.get_text().strip() for th in tb.select("thead th")]
            if spec["header"] not in ths: continue
            ci = ths.index(spec["header"]); cnt = Counter()
            for tr in tb.select("tbody tr"):
                tds = tr.find_all("td")
                if len(tds) <= ci: continue
                txt = tds[ci].get_text().strip()
                r = next((r for r in spec["rules"] if txt.startswith(r[0])), None)
                if not r: continue
                tr["class"] = tr.get("class", []) + [f"row-{r[1]}"]; tds[ci]["class"] = tds[ci].get("class", []) + ["rt", f"rt-{r[1]}"]
                cnt[r[1]] += 1; n_tag += 1
                if spec.get("inherit"): name_map[tds[0].get_text().strip()] = r[1]
            if spec.get("filter") and cnt:
                bar = soup.new_tag("div", attrs={"class": "row-filter", "role": "group", "aria-label": "按结论筛选"})
                total = len(tb.select("tbody tr"))
                b0 = soup.new_tag("button", attrs={"class": "rf-btn on", "data-f": "all", "type": "button"}); b0.string = f"全部 {total}"; bar.append(b0)
                for r in spec["rules"]:
                    if cnt[r[1]]:
                        b = soup.new_tag("button", attrs={"class": f"rf-btn rf-{r[1]}", "data-f": r[1], "type": "button"})
                        b.string = f"{r[2] if len(r) > 2 else r[0]} {cnt[r[1]]}"; bar.append(b)
                tb["data-filter"] = "1"; tb.insert_before(bar); filters += 1
        if spec.get("inherit") and name_map:
            for tb in tables:
                ths = [th.get_text().strip() for th in tb.select("thead th")]
                if spec["header"] in ths or not ths: continue
                rows = tb.select("tbody tr")
                hits = []
                for tr in rows:
                    nm = tr.find("td").get_text().strip() if tr.find("td") else ""
                    toks = _norm_name(nm)
                    cands = {name_map[nm]} if nm in name_map else {c for k, c in name_map.items()
                             if any(t in k or any(t2 in t for t2 in _norm_name(k) if len(t2) >= 3) for t in toks)}
                    hits.append((tr, cands))
                if sum(1 for _, c in hits if len(c) == 1) < len(rows) * 0.8: continue   # not a table about the same products
                used = []
                for tr, c in hits:
                    if len(c) == 1:
                        cls = c.pop(); tr["class"] = tr.get("class", []) + [f"row-{cls}", "row-inh"]; n_inh += 1
                        if cls not in used: used.append(cls)
                lg = soup.new_tag("div", attrs={"class": "tbl-legend"})
                for cls in used:
                    lab = next((r[2] if len(r) > 2 else r[0]) for r in spec["rules"] if r[1] == cls)
                    sp_ = soup.new_tag("span", attrs={"class": f"grp-{cls}"}); sp_.string = lab; lg.append(sp_)
                if spec.get("inherit_note"):
                    sp_ = soup.new_tag("em"); sp_.string = spec["inherit_note"]; lg.append(sp_)
                tb.insert_before(lg)
    return n_tag, n_inh, filters


def versus_tables(soup, spec):
    """{heading keyword: [cls_a, cls_b]}: a 3-column table (维度 | A | B) under that heading -> side-by-side grid."""
    n = 0
    for kw, cls in spec.items():
        for h in soup.find_all(["h2", "h3", "h4"]):
            if kw not in h.get_text(): continue
            tb = h.find_next_sibling(["table", "h2", "h3"])
            if tb is None or tb.name != "table": continue
            ths = tb.select("thead th")
            if len(ths) != 3: continue
            labels = [th.get_text().strip() for th in ths]
            box = soup.new_tag("div", attrs={"class": "vs-table"})
            head = soup.new_tag("div", attrs={"class": "vs-row vs-head"})
            for i, th in enumerate(ths):
                c = soup.new_tag("div", attrs={"class": ["vs-dim"] if i == 0 else ["vs-col", f"grp-{cls[i-1]}"]})
                for x in list(th.contents): c.append(x.extract())
                head.append(c)
            box.append(head)
            for tr in tb.select("tbody tr"):
                tds = tr.find_all("td"); row = soup.new_tag("div", attrs={"class": "vs-row"})
                for i, td in enumerate(tds[:3]):
                    c = soup.new_tag("div", attrs={"class": ["vs-dim"] if i == 0 else ["vs-col", f"grp-{cls[i-1]}"]})
                    if i:
                        lab = soup.new_tag("span", attrs={"class": "vs-lab"}); lab.string = labels[i]; c.append(lab)
                    for x in list(td.contents): c.append(x.extract())
                    row.append(c)
                box.append(row)
            tb.replace_with(box); n += 1
    return n


def wrap_badges(soup, markers):
    counts = Counter()
    kw_re = "|".join(re.escape(k) for k, _ in markers)
    pat = re.compile(r"(?:\[([^\[\]]{0,12}?(?:%s)[^\[\]]{0,40})\]|【([^【】]{0,12}?(?:%s)[^【】]{0,40})】)" % (kw_re, kw_re))

    def cls_for(s):
        for k, c in markers:
            if k in s:
                return c
        return "note"

    # 1) <strong>[xxx]</strong> -> badge
    for st in soup.find_all(["strong", "b"]):
        t = st.get_text()
        m = re.fullmatch(r"\s*[\[【]([^\[\]【】]+)[\]】]\s*", t)
        if VERDICT_RE.match(t.strip()):
            counts["ok"] += 1
            span = soup.new_tag("span", attrs={"class": "badge badge-ok", "title": MARKER_LABEL["ok"]})
            span.string = t.strip(); st.replace_with(span); continue
        if m and pat.fullmatch("[" + m.group(1) + "]"):
            c = cls_for(m.group(1)); counts[c] += 1
            span = soup.new_tag("span", attrs={"class": f"badge badge-{c}", "title": MARKER_LABEL[c]})
            span.string = m.group(1)
            st.replace_with(span)
    # 2) plain-text [xxx] inside text nodes (skip code/pre/a/headings get them too)
    for node in list(soup.find_all(string=pat)):
        if node.parent.name in ("code", "pre", "script", "style") or node.find_parent("pre"):
            continue
        parts, last, s = [], 0, str(node)
        for m in pat.finditer(s):
            parts.append(NavigableString(s[last:m.start()]))
            inner = m.group(1) or m.group(2)
            c = cls_for(inner); counts[c] += 1
            span = soup.new_tag("span", attrs={"class": f"badge badge-{c}", "title": MARKER_LABEL[c]})
            span.string = inner
            parts.append(span); last = m.end()
        parts.append(NavigableString(s[last:]))
        for p in parts:
            node.insert_before(p)
        node.extract()
    return counts


def build(md_path, out_dir, meta_path=None, hero_path=None, embed_hero=True, template=None, parts=False, meta_override=None):
    """parts=True: return the rendered pieces (body, TOC, header bits, stats) instead of writing a page.
    Used by scripts/new_report.py to produce a Hugo content bundle."""
    raw = open(md_path, encoding="utf-8").read()
    fm, body_md = split_front_matter(raw)
    meta = dict(fm)
    if meta_path:
        meta.update(yaml.safe_load(open(meta_path, encoding="utf-8")) or {})
    if meta_override:
        meta.update(meta_override)
    # No front matter and a single leading "# Title" line: use it as the title and treat "##" as
    # top-level sections (heading shift 0) instead of shifting everything down one level.
    shift = meta.get("heading_shift")
    no_code = re.sub(r"(?ms)^```.*?^```", "", body_md)
    m_t = re.match(r"\s*#\s+(.+?)\s*\n", body_md)
    if m_t and len(re.findall(r"(?m)^#\s", no_code)) == 1:
        meta.setdefault("title", m_t.group(1))
        body_md = body_md[m_t.end():]
        if shift is None: shift = 0
    if shift is None: shift = 1
    title = str(meta.get("title") or "未命名报告")
    date = str(meta.get("date") or dt.date.today().isoformat())
    d = dt.date.fromisoformat(date[:10])

    soup = BeautifulSoup(pandoc(body_md, int(shift)), "html.parser")

    # ---- lead blockquote(s) before first h2 -> note box
    for el in list(soup.contents):
        if getattr(el, "name", None) == "h2":
            break
        if getattr(el, "name", None) == "blockquote":
            el["class"] = ["lead-note"]

    # ---- quick card source: meta.quick > "## 一分钟速览" section in md > bold leads of key conclusions
    quick = meta.get("quick") or []
    for h in soup.find_all("h2"):
        if "速览" in h.get_text():
            ul = h.find_next_sibling(["ul", "ol"])
            if not quick and ul:
                quick = [li.decode_contents() for li in ul.find_all("li", recursive=False)]
            if ul: ul.decompose()
            h.decompose()
            break

    # ---- headings: ids + section numbers
    used = set()
    h2s = soup.find_all("h2")
    toc_levels = ["h2", "h3"] + (["h4"] if meta.get("toc_h4") else [])
    parent_id, sub_n = None, 0
    for i, h in enumerate(soup.find_all(toc_levels)):
        t = h.get_text().strip()
        no, rest = secno_and_rest(t)
        if h.name == "h4" and not no and parent_id:   # unnumbered h4 under a numbered h3 -> sec-2-1-3
            sub_n += 1; hid = f"{parent_id}-{sub_n}"
        else:
            hid = ("sec-" + no.replace(".", "-")) if no else ("sec-x%d" % i)
        while hid in used:
            hid += "-b"
        used.add(hid); h["id"] = hid
        if h.name in ("h2", "h3"): parent_id, sub_n = hid, 0
        h["data-toc"] = rest if no is None else f"{no} {rest}"
        if no:
            h.clear()
            sn = soup.new_tag("span", attrs={"class": "secno"}); sn.string = no
            h.append(sn); h.append(NavigableString(rest))

    def section_children(h2):
        out = []
        for sib in h2.next_siblings:
            if getattr(sib, "name", None) == "h2":
                break
            out.append(sib)
        return out

    card_kw = meta.get("card_sections", ["拆解"])
    topic_kw = meta.get("topic_sections", ["专题"])
    kc_kw = meta.get("key_sections", ["关键结论", "核心结论", "要点"])
    src_kw = meta.get("source_sections", ["来源"])
    sup_kw = meta.get("supplement_sections", ["补充"])
    # sources block = LAST top-level heading containing a source keyword (it need not be the last chapter)
    src_h2 = None
    for _h in soup.find_all("h2"):
        if any(k in _h.get_text() for k in src_kw):
            src_h2 = _h

    # key-conclusion list: first ol/ul directly after an h2/h3 whose title has a key keyword -> card grid
    for hk in soup.find_all(["h2", "h3"]):
        if any(k in hk.get_text() for k in kc_kw):
            ol = hk.find_next_sibling(["ol", "ul", "h2", "h3"])
            if ol is not None and ol.name in ("ol", "ul"):
                ol["class"] = ["kc-grid"]
                if not quick:
                    for li in ol.find_all("li", recursive=False):
                        st = li.find("strong")
                        if st: quick.append(st.decode_contents())
    for h2 in soup.find_all("h2"):
        t = h2.get_text()
        is_sup = any(k in t for k in sup_kw) and h2 is not src_h2
        if is_sup:
            h2["class"] = h2.get("class", []) + ["sup-h2"]
        if any(k in t for k in card_kw + topic_kw) or is_sup:
            is_card = any(k in t for k in card_kw) and not is_sup
            kids = section_children(h2)
            groups, cur = [], None
            card_h = meta.get("card_heading", "h3") if is_card else "h3"
            for k in kids:
                nm = getattr(k, "name", None)
                if nm == card_h:
                    cur = [k]; groups.append(cur)
                elif card_h == "h4" and nm == "h3":
                    cur = None          # a subsection heading (e.g. 海外 / 国内) ends the current card
                elif cur is not None:
                    cur.append(k)
            grp = next((g_ for g_ in meta.get("card_groups", []) if g_[0] in t), None) if is_card else None
            if grp:
                h2["class"] = h2.get("class", []) + ["grp-h2", f"grp-{grp[1]}"]; h2["data-grp"] = grp[1]
                chip = soup.new_tag("span", attrs={"class": f"grp-count grp-{grp[1]}"})
                chip.string = f"{len(groups)} 张卡片"; h2.append(chip)
            for g in groups:
                wrap = soup.new_tag("section", attrs={"class": "p-card" if is_card else ("s-card" if is_sup else "topic")})
                if grp:
                    wrap["class"] = ["p-card", f"grp-{grp[1]}"]
                g[0].insert_before(wrap)
                for el in g:
                    wrap.append(el.extract())
                if is_card:
                    h3 = wrap.find(card_h)
                    sn = h3.find("span", class_="secno")
                    txt = h3.get_text()[len(sn.get_text()):] if sn else h3.get_text()
                    if "：" in txt:
                        v, p = txt.split("：", 1)
                        for c in list(h3.contents):
                            if c is not sn: c.extract()
                        a = soup.new_tag("span", attrs={"class": "vendor"}); a.string = v.strip()
                        b = soup.new_tag("span", attrs={"class": "prod"}); b.string = p.strip()
                        h3.append(a); h3.append(b)
                    if grp:
                        lab = soup.new_tag("span", attrs={"class": f"grp-chip grp-{grp[1]}"}); lab.string = grp[2]
                        (sn.insert_after(lab) if sn else h3.insert(0, lab))
        if h2 is src_h2:
            box = soup.new_tag("div", attrs={"class": "sources-block"})
            kids = section_children(h2)
            h2.insert_after(box)
            for k in kids:
                box.append(k.extract())

    # ---- mermaid
    n_diag = 0
    for pre in soup.find_all("pre", class_="mermaid"):
        n_diag += 1
        src = sanitize_mermaid(pre.get_text())
        fig = soup.new_tag("figure", attrs={"class": "diagram", "id": f"diagram-{n_diag}", "data-src": src})
        p = soup.new_tag("pre", attrs={"class": "mermaid"}); p.string = src
        cap = soup.new_tag("figcaption"); cap.string = f"图 {n_diag}"
        fig.append(p); fig.append(cap)
        pre.replace_with(fig)
    # plain code blocks tagged ```mermaid can also come out as <pre><code class="language-mermaid">
    for code in soup.select("pre > code.language-mermaid"):
        code.parent["class"] = ["mermaid"]

    # ---- paragraphs that are just one bold line act as mini-headings
    for p in soup.find_all("p"):
        kids = [c for c in p.contents if not (isinstance(c, NavigableString) and not c.strip())]
        if len(kids) == 1 and getattr(kids[0], "name", None) == "strong":
            p["class"] = p.get("class", []) + ["lead-h"]

    # ---- product-card field blocks + roadmap mini timelines; correction boxes
    n_cblk, n_roadmap = enhance_cards(soup, [tuple(x) for x in meta.get("card_blocks", DEFAULT_CARD_BLOCKS)]) \
        if meta.get("card_field_blocks", True) else (0, 0)
    n_updblk = mark_update_blocks(soup, meta.get("update_blocks", []))

    # ---- timeline-shaped tables -> timeline cards; other tables -> enhanced scroll boxes
    n_tl_v, n_tl_s = convert_timelines(soup) if meta.get("timeline_tables", True) else (0, 0)
    n_vs = versus_tables(soup, meta.get("versus_tables") or {})
    n_rowtag, n_rowinh, n_filters = tag_table_rows(soup, meta.get("row_tags") or [])
    n_tables = n_vs
    for tb in soup.find_all("table"):
        n_tables += 1
        w = soup.new_tag("div", attrs={"class": " ".join(enhance_table(soup, tb, int(meta.get("tall_table_rows", 12)))), "tabindex": "0"})
        tb.wrap(w)

    # ---- links open in new tab, collect domains
    domains = Counter(); n_links = 0
    for a in soup.find_all("a", href=True):
        u = urlparse(a["href"])
        if u.scheme in ("http", "https"):
            n_links += 1
            domains[u.netloc.lower().removeprefix("www.")] += 1
            a["target"] = "_blank"; a["rel"] = "noopener"

    # ---- badges (after structure so headings/cards keep them)
    markers = [tuple(x) for x in meta.get("markers", DEFAULT_MARKERS)] + [tuple(x) for x in meta.get("extra_markers", [])]
    n_updates = mark_update_notes(soup, meta.get("update_patterns", DEFAULT_UPDATE_PATTERNS)) + n_updblk
    counts = wrap_badges(soup, markers)
    # heading_notes: {heading id: note text}. Appends a visible correction callout to a
    # heading (and its TOC entry) whose verbatim title would otherwise read as stale.
    # The note text should itself be quoted verbatim from the source.
    n_hnotes = 0
    for hid, note in (meta.get("heading_notes") or {}).items():
        h = soup.find(id=hid)
        if not h:
            print(f"WARN heading_notes: no heading #{hid}", file=sys.stderr); continue
        sp = soup.new_tag("span", attrs={"class": "upd-note heading-note"}); sp.string = note
        h.append(NavigableString(" ")); h.append(sp)
        if h.get("data-toc"): h["data-toc"] += " " + note
        n_hnotes += 1
    # don't count the legend inside the lead note
    legends = soup.find_all("blockquote", class_="lead-note") + [
        bq for bq in soup.find_all("blockquote") if re.search(r"标注(约定)?\s*[：:]", bq.get_text()) and "lead-note" not in (bq.get("class") or [])]
    # only badges that *define* a marker (first thing in a legend list item, e.g. "- **[二手]**：…") are
    # excluded; real markers elsewhere in the lead note (e.g. 【待核实：汇率…】) still count
    for ln in legends:
        for sp in ln.find_all("span", class_="badge"):
            li = sp.find_parent("li")
            first = None
            if li:
                for c_ in li.descendants:
                    if isinstance(c_, NavigableString) and not c_.strip():
                        continue
                    first = c_; break
            if li and (first is sp or (first is not None and getattr(first, "find", None) and first.find("span", class_="badge") is sp and not first.get_text().replace(sp.get_text(), "").strip()) or (isinstance(first, NavigableString) and first.parent is sp)):
                counts[sp["class"][1].split("-", 1)[1]] -= 1

    # no dedicated sources chapter: optionally append an auto-generated domain summary (labelled as such)
    sb = soup.find("div", class_="sources-block")
    if sb is None and meta.get("sources_fallback"):
        fb = meta["sources_fallback"] if isinstance(meta["sources_fallback"], dict) else {}
        h = soup.new_tag("h2", attrs={"id": "sec-sources-auto", "class": "auto-h",
                                      "data-toc": fb.get("toc", "信源汇总（自动生成）")})
        h.string = fb.get("title", "信源汇总（自动生成）")
        sb = soup.new_tag("div", attrs={"class": "sources-block auto"})
        note = soup.new_tag("p", attrs={"class": "auto-note"})
        note.string = fb.get("note", "原文没有独立的来源章节，来源分散在各节的「来源」条目中；下面按域名自动汇总全文链接，不含新增信息。")
        sb.append(note)
        soup.append(h); soup.append(sb)
    # domain cloud into sources block
    cloud = soup.new_tag("div", attrs={"class": "domain-cloud"})
    for dom, c in domains.most_common():
        s = soup.new_tag("span"); s.string = dom
        b = soup.new_tag("b"); b.string = str(c); s.append(b); cloud.append(s)
    if sb:
        lab = soup.new_tag("p"); lab.string = f"全文共引用 {n_links} 条链接、{len(domains)} 个域名（数字为引用次数）："
        sb.append(lab); sb.append(cloud)

    # ---- TOC (h2 > h3 > optional h4)
    lv = {"h2": 1, "h3": 2, "h4": 3}
    toc, depth, cur_grp = [], 0, None
    for h in soup.find_all(toc_levels):
        if not h.get("id"): continue
        label = html.escape(h.get("data-toc", h.get_text()))
        if h.has_attr("data-toc"): del h["data-toc"]
        L = lv[h.name]
        if L > depth:
            toc.append("<ul>" * (L - depth))
        else:
            toc.append("</li>")
            if L < depth: toc.append("</ul></li>" * (depth - L))
        depth = L
        if L == 1: cur_grp = h.get("data-grp")
        gcls = f" toc-grp grp-{cur_grp}" if cur_grp else ""
        toc.append(f'<li class="toc-l{L}{gcls}"><a href="#{h["id"]}">{label}</a>')
    toc.append("</li>" + "</ul></li>" * (depth - 1) + "</ul>" if depth else "")
    body_html = str(soup)
    plain = soup.get_text(" ")

    # ---- header pieces
    tags = meta.get("tags") or []
    tags_html = "".join(f'<span class="tag {TAG_COLORS[i % 3]}">{html.escape(str(t))}</span>' for i, t in enumerate(tags))
    mb = ['<div class="marker-bar" aria-label="证据标注统计"><span class="mb-label">证据标注</span>']
    for c in ["verify", "second", "infer", "self", "note", "ok"]:
        if counts.get(c):
            mb.append(f'<span class="badge badge-{c} mb-pill">{MARKER_LABEL[c]}<b>{counts[c]}</b></span>')
    if n_updates:
        mb.append(f'<span class="badge badge-upd mb-pill">更新/更正<b>{n_updates}</b></span>')
    mb.append(f'<span class="mb-sep"></span><span class="mb-src">{n_diag} {meta.get("diagram_label", "张架构图")}'
              + (f' · {n_tables} 张表格' if meta.get("show_table_count") else '') + f' · {len(domains)} 个信源</span></div>')

    hero_html = ""
    if hero_path:
        alt = html.escape(str(meta.get("hero_alt", title)))
        cap = html.escape(str(meta.get("hero_caption", "")))
        if embed_hero:
            data, mime = open(hero_path, "rb").read(), "image/png"
            try:
                from PIL import Image
                im = Image.open(io.BytesIO(data)).convert("RGB"); bio = io.BytesIO()
                im.save(bio, "WEBP", quality=86); data, mime = bio.getvalue(), "image/webp"
            except Exception:
                pass
            src = f"data:{mime};base64," + base64.b64encode(data).decode()
        else:
            src = os.path.relpath(os.path.abspath(hero_path), os.path.abspath(out_dir))
        hero_html = (f'<figure class="article-hero"><img src="{src}" alt="{alt}" width="1600" height="900" data-zoom '
                     f'title="点击查看大图">' + (f"<figcaption>{cap}</figcaption>" if cap else "") + "</figure>")

    quick_html = ""
    if quick:
        lis = "".join(f"<li>{q}</li>" for q in quick)
        qs = BeautifulSoup(f"<ul>{lis}</ul>", "html.parser"); wrap_badges(qs, markers)
        quick_html = f'<section class="quick" id="quick"><div class="quick-h">一分钟速览 <span class="pill">TL;DR</span></div>{qs}</section>'

    site = str(meta.get("site_name", "行业深读"))
    subtitle = meta.get("subtitle")
    repl = {
        "TITLE": html.escape(title), "SITE_NAME": html.escape(site),
        "SITE_NAME_HTML": html.escape(site).replace("·", '<span class="dot"></span>', 1) if "·" in site else html.escape(site) + '<span class="dot"></span>',
        "SUMMARY": html.escape(str(meta.get("summary", ""))), "SUMMARY_ATTR": html.escape(str(meta.get("summary", "")), quote=True),
        "SUBTITLE_HTML": f'<p class="article-subtitle">{html.escape(str(subtitle))}</p>' if subtitle else "",
        "DATE": date, "DATE_CN": f"{d.year} 年 {d.month:02d} 月 {d.day:02d} 日", "WEEKDAY": WEEKDAYS[d.weekday()],
        "READ_MIN": str(text_len_minutes(plain)), "SOURCE_COUNT": str(len(domains)), "LINK_COUNT": str(n_links),
        "TAGS": tags_html, "MARKER_BAR": "".join(mb), "HERO": hero_html, "QUICK": quick_html,
        "BODY": body_html, "TOC": "".join(toc), "MERMAID_URL": meta.get("mermaid_url", MERMAID_URL),
        "FOOTER": html.escape(str(meta.get("footer", f"{title} · 源文件 {os.path.basename(md_path)} · 由 build.py 生成"))),
    }
    stats = {"diagrams": n_diag, "links": n_links, "domains": len(domains),
             "badges": dict(counts), "quick_items": len(quick), "read_min": repl["READ_MIN"],
             "cards": len(soup.select("section.p-card")), "topics": body_html.count('class="topic"'),
             "supplement_cards": body_html.count('class="s-card"'), "update_notes": n_updates, "heading_notes": n_hnotes,
             "tables": n_tables, "card_blocks": n_cblk, "roadmaps": n_roadmap, "update_blocks": n_updblk, "versus_tables": n_vs,
             "row_tags": n_rowtag, "row_tags_inherited": n_rowinh, "row_filters": n_filters, "timeline_vendor_cards": n_tl_v,
             "timeline_stages": n_tl_s, "sources_heading": src_h2.get_text() if src_h2 else None}
    if parts:
        return {"meta": meta, "title": title, "date": date, "tags": [str(t) for t in tags], "quick_html": quick_html,
                "body_html": body_html, "toc_html": "".join(toc), "marker_bar_html": "".join(mb), "stats": stats,
                "mermaid_url": repl["MERMAID_URL"], "subtitle": subtitle}
    tpl = open(template or os.path.join(HERE, "standalone-template.html"), encoding="utf-8").read()
    out = re.sub(r"\{\{([A-Z_]+)\}\}", lambda m: repl.get(m.group(1), m.group(0)), tpl)
    os.makedirs(out_dir, exist_ok=True)
    op = os.path.join(out_dir, "index.html")
    open(op, "w", encoding="utf-8").write(out)
    stats = {"out": op, "bytes": len(out.encode()), "diagrams": n_diag, "links": n_links, "domains": len(domains),
             "badges": dict(counts), "quick_items": len(quick), "read_min": repl["READ_MIN"],
             "cards": len(soup.select("section.p-card")), "topics": body_html.count('class="topic"'),
             "supplement_cards": body_html.count('class="s-card"'), "update_notes": n_updates, "heading_notes": n_hnotes,
             "tables": n_tables, "card_blocks": n_cblk, "roadmaps": n_roadmap, "update_blocks": n_updblk, "versus_tables": n_vs, "row_tags": n_rowtag, "row_tags_inherited": n_rowinh, "row_filters": n_filters, "timeline_vendor_cards": n_tl_v, "timeline_stages": n_tl_s,
             "sources_heading": src_h2.get_text() if src_h2 else None}
    print(json.dumps(stats, ensure_ascii=False))
    return stats


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("markdown"); ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--meta"); ap.add_argument("--hero"); ap.add_argument("--template")
    ap.add_argument("--no-embed-hero", action="store_true", help="link hero by relative path instead of base64")
    a = ap.parse_args()
    build(a.markdown, a.out, a.meta, a.hero, not a.no_embed_hero, a.template)
