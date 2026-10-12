#!/usr/bin/env python3
"""新增或更新一篇报告：Markdown + meta.yaml (+ hero.png) -> Hugo 内容包 content/reports/<slug>/。

用法：
    python3 scripts/new_report.py 报告.md --slug my-report --section research --meta meta.yaml --hero hero.png   # 新增/更新
    python3 scripts/new_report.py --rebuild-all                                              # 按 reports-src/ 全部重渲染
    加 --check-build：渲染后跑一次 hugo 构建确认没坏
    --section：栏目 research=专题调研 / tracking=追踪对比 / daily=每日 AI 简报 / notes=学习笔记
               （写进 reports-src/<slug>/meta.yaml 的 section；之后 --rebuild-all 沿用）
    meta.yaml 的 topics：从统一话题 Agent / 大模型 / 工作流 / 个人 Agent / 基础设施 / 商业化 中选，排在具体 tags 前

做的事：
  1. 把源文件、meta.yaml、hero.png 复制到 reports-src/<slug>/（仓库里留一份可重渲染的输入；原文件不动）
  2. 用 scripts/reportlib/build.py（与单页版同一套渲染逻辑：证据徽章、卡片、时间线、表格、mermaid、$ 修复）
     把正文预渲染成 HTML，写入 content/reports/<slug>/index.html（YAML front matter + HTML 正文）
  3. 把 hero.png 放进同一个内容包，由 Hugo 在构建时转成 WebP
  4. 自检：原文里的【…】证据标注数 == 页面徽章数，否则报错退出（退出码 1）

退出码：0 成功；1 输入/校验失败；3 hugo 构建失败
"""
from __future__ import annotations

import argparse, re, shutil, subprocess, sys
from pathlib import Path

import yaml
from bs4 import BeautifulSoup

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts" / "reportlib"))
import build as rb  # noqa: E402

SRC_DIR = REPO / "reports-src"
CONTENT = REPO / "content" / "reports"
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,60}$")
# 栏目（按内容形态）：键 = URL 段 /research/ 等；栏目页在 content/categories/<键>/_index.md
SECTIONS = {"research": "专题调研", "tracking": "追踪对比", "daily": "每日 AI 简报", "notes": "学习笔记"}
# 统一话题标签：meta.yaml 的 topics 只能从这里选，会排在具体标签前面
TOPICS = ["Agent", "大模型", "工作流", "个人 Agent", "基础设施", "商业化"]


def fail(msg, code=1):
    print(f"错误：{msg}", file=sys.stderr)
    sys.exit(code)


def count_source_markers(md: str, meta: dict) -> tuple[int, list[str]]:
    """Count evidence markers straight from the Markdown with the same keyword list the renderer uses.
    Returns (expected badge count, 【…】 markers that match no keyword)."""
    body = re.sub(r"(?ms)^```.*?^```", "", rb.split_front_matter(md)[1])
    body = re.sub(r"`[^`\n]*`", "", body)
    body = re.sub(r"\[[^\[\]\n]*\]\([^)\s]*\)", "", body)   # link texts such as [价格（二手）](url) render as links
    markers = [tuple(x) for x in meta.get("markers", rb.DEFAULT_MARKERS)] + [tuple(x) for x in meta.get("extra_markers", [])]
    kw = "|".join(re.escape(k) for k, _ in markers)
    pat = re.compile(r"(?:\[([^\[\]]{0,12}?(?:%s)[^\[\]]{0,40})\]|【([^【】]{0,12}?(?:%s)[^【】]{0,40})】)" % (kw, kw))
    n = len(pat.findall(body))
    n += len(re.findall(r"\*\*(?:已核实|部分核实)(?:（[^（）]{0,20}）)?\*\*", body))
    unknown = [m for m in re.findall(r"【[^】\n]{1,60}】", body) if not pat.fullmatch(m)]
    return n, unknown


def set_meta_key(meta_p: Path, key: str, value: str):
    """Set a top-level scalar in reports-src/<slug>/meta.yaml without reformatting the rest of the file."""
    txt = meta_p.read_text(encoding="utf-8") if meta_p.exists() else ""
    line = f"{key}: {value}"
    if re.search(rf"(?m)^{key}:.*$", txt):
        txt = re.sub(rf"(?m)^{key}:.*$", line, txt, count=1)
    else:
        txt = line + "\n" + txt
    meta_p.write_text(txt, encoding="utf-8")


def render(slug: str) -> dict:
    d = SRC_DIR / slug
    md = d / "report.md"
    meta_p = d / "meta.yaml"
    if not md.exists():
        fail(f"{md} 不存在")
    parts = rb.build(str(md), None, str(meta_p) if meta_p.exists() else None, parts=True)
    meta = parts["meta"]

    soup = BeautifulSoup(parts["body_html"], "html.parser")
    n_badges = len(soup.select(".badge"))
    n_src, unknown = count_source_markers(md.read_text(encoding="utf-8"), meta)
    if unknown:
        fail(f"{slug}：这些【…】标注没有匹配任何徽章关键词，会以普通文字显示：{sorted(set(unknown))}；在 meta.yaml 的 extra_markers 里补上")
    if n_badges != n_src:
        fail(f"{slug}：原文按关键词应有 {n_src} 个证据标注，页面只有 {n_badges} 个徽章")

    section = str(meta.get("section") or "")
    if section not in SECTIONS:
        fail(f"{slug}：栏目 section 必须是 {list(SECTIONS)} 之一（用 --section 指定，或写进 meta.yaml），现在是 {section!r}")
    topics = [str(t) for t in (meta.get("topics") or [])]
    bad = [t for t in topics if t not in TOPICS]
    if bad:
        fail(f"{slug}：topics 里有不在统一话题表里的标签 {bad}；可选：{TOPICS}（具体标签请写在 tags）")
    tags = topics + [t for t in parts["tags"] if t not in topics]

    date = parts["date"]
    if len(date) == 10:
        date += "T09:00:00+08:00"
    fm = {
        "title": parts["title"],
        "date": date,
        "slug": slug,
        "summary": str(meta.get("summary", "")),
        "description": str(meta.get("summary", "")),
        "tags": tags,
        "categories": [section],
        "build": {"publishResources": False},   # only the WebP versions Hugo generates get published
        "params": {
            "subtitle": str(parts["subtitle"]) if parts["subtitle"] else "",
            "read_min": int(parts["stats"]["read_min"]),
            "link_count": parts["stats"]["links"],
            "source_count": parts["stats"]["domains"],
            "has_mermaid": parts["stats"]["diagrams"] > 0,
            "mermaid_url": parts["mermaid_url"],
            "hero_alt": str(meta.get("hero_alt", parts["title"])),
            "hero_caption": str(meta.get("hero_caption", "")),
            "footer": str(meta.get("footer", "")),
            "marker_bar_html": parts["marker_bar_html"],
            "quick_html": parts["quick_html"],
            "toc_html": parts["toc_html"],
            "stats": parts["stats"],
        },
    }
    out = CONTENT / slug
    out.mkdir(parents=True, exist_ok=True)
    head = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False, width=10**9)
    (out / "index.html").write_text(f"---\n{head}---\n{parts['body_html']}\n", encoding="utf-8")
    for old in out.glob("hero.*"):
        old.unlink()
    for h in d.glob("hero.*"):
        shutil.copy2(h, out / h.name)
    st = parts["stats"]
    print(f"✓ {slug}: {st['diagrams']} 图 · {st['tables']} 表 · {st['cards']} 卡片 · 徽章 {n_badges}/{n_src} · {st['links']} 链接")
    return parts


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("markdown", nargs="?")
    ap.add_argument("--slug")
    ap.add_argument("--meta")
    ap.add_argument("--hero")
    ap.add_argument("--section", choices=list(SECTIONS), help="栏目：" + "，".join(f"{k}={v}" for k, v in SECTIONS.items()))
    ap.add_argument("--rebuild-all", action="store_true")
    ap.add_argument("--check-build", action="store_true")
    a = ap.parse_args()

    if a.rebuild_all:
        if a.section:
            fail("--section 只用于单篇；批量重渲染时栏目取各自 meta.yaml 的 section")
        slugs = sorted(p.name for p in SRC_DIR.iterdir() if (p / "report.md").exists())
    else:
        if not a.markdown or not a.slug:
            fail("需要 报告.md 和 --slug（或用 --rebuild-all）")
        if not SLUG_RE.match(a.slug):
            fail("slug 只能用小写字母、数字和连字符，例如 personal-agents")
        d = SRC_DIR / a.slug
        d.mkdir(parents=True, exist_ok=True)
        shutil.copy2(a.markdown, d / "report.md")
        if a.meta:
            shutil.copy2(a.meta, d / "meta.yaml")
        if a.section:
            set_meta_key(d / "meta.yaml", "section", a.section)
        if a.hero:
            for old in d.glob("hero.*"):
                old.unlink()
            shutil.copy2(a.hero, d / ("hero" + Path(a.hero).suffix.lower()))
        slugs = [a.slug]
    for s in slugs:
        render(s)
    if a.check_build:
        hugo = shutil.which("hugo") or "/workspace/tools/hugo"
        r = subprocess.run([hugo, "--minify", "--quiet", "-d", str(REPO / ".check-public")], cwd=REPO)
        shutil.rmtree(REPO / ".check-public", ignore_errors=True)
        if r.returncode:
            fail("hugo 构建失败", 3)
        print("✓ hugo 构建通过")


if __name__ == "__main__":
    main()
