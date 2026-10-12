# Shuang · 行业深读（Hugo + GitHub Pages）

把 Markdown 调研报告发布成静态站点：首页报告卡片、标签页、Pagefind 全文搜索、RSS，
每篇报告保留单页版的全部样式（Ghost Protocol 配色、亮/暗切换、浮动目录、速览卡片、
证据标注徽章、产品卡片与时间线、mermaid 图、粘性表头、大厂/初创分组与行筛选）。

- 报告地址：`/reports/<slug>/`
- 标签：`/tags/`；搜索：`/search/`；RSS：`/index.xml`

## 目录结构

```
hugo.toml                  站点配置（baseURL 占位符在这里）
content/reports/<slug>/    每篇报告一个内容包：index.html（脚本生成，勿手改）+ hero.png
reports-src/<slug>/        生成用的输入：report.md、meta.yaml、hero.png（可重渲染）
scripts/new_report.py      新增/更新报告的唯一入口
scripts/reportlib/         渲染逻辑（与单页版 build.py 同源）
layouts/                   手写模板（baseof / home / list / taxonomy / search / reports/single）
assets/css, assets/js      报告样式与交互
.github/workflows/deploy.yml   推送 main 自动构建并发布
```

## 新增一篇报告（一条命令）

准备好 Markdown、`meta.yaml`（参考 `scripts/meta.example.yaml`）和可选的封面 `hero.png`：

```bash
python3 scripts/new_report.py 报告.md --slug my-report --meta meta.yaml --hero hero.png --check-build
git add -A && git commit -m "新增报告：my-report" && git push
```

脚本会：

1. 把三份输入复制到 `reports-src/my-report/`（原文件不动）；
2. 用与单页版相同的渲染逻辑把正文预渲染成 HTML，写入 `content/reports/my-report/index.html`；
3. 把 hero.png 放进内容包，Hugo 构建时自动转 WebP（没有封面时首页显示渐变占位）；
4. 自检：原文中的证据标注数（【待核实】等）必须等于页面徽章数，否则报错退出；
5. 带 `--check-build` 时再跑一次 hugo 构建确认没坏。

更新已有报告：用同一个 slug 再跑一次即可。改了模板或渲染逻辑后全部重渲染：

```bash
python3 scripts/new_report.py --rebuild-all
```

为什么是"预渲染"而不是让 Hugo 直接渲染 Markdown：报告里有大量证据徽章、卡片、时间线、
分组表格等定制结构，单页版的渲染管线已验证过，直接复用最稳；Hugo 只负责外壳、列表、标签、RSS。
代价是本地新增报告时需要 Python 和 pandoc（CI 不需要）。

本地依赖（只有跑 new_report.py 时需要）：

```bash
pip install -r scripts/requirements.txt    # beautifulsoup4、PyYAML
# 另需 pandoc 3.x（可用环境变量 PANDOC 指定路径）
```

## 本地预览

只看排版（热更新，搜索不可用）：

```bash
hugo server            # http://localhost:1313/ai-radar/ （路径随 hugo.toml 的 baseURL）
```

含搜索的完整预览（Pagefind 索引只在构建后生成）：

```bash
hugo --minify --baseURL http://localhost:8080/
pagefind --site public
python3 -m http.server 8080 -d public
```

需要 Hugo **extended** ≥ 0.146（用到新版模板目录结构；开发时用的是 0.167.0）和 Pagefind ≥ 1.0
（建议 extended 版，带中文分词）。

## 部署到 GitHub Pages

1. 新建**公开**仓库并推送本目录（`main` 分支）。
2. 仓库 Settings → Pages → Build and deployment → Source 选 **GitHub Actions**。
3. 之后每次推送 `main`（或在 Actions 页手动 Run workflow）都会：安装 Hugo + Pagefind → `hugo --minify` → `pagefind --site public` → 发布。

baseURL：`hugo.toml` 里是 `https://loushang0826.github.io/ai-radar/`。CI 会用 Pages 的实际地址覆盖它，
所以不改也能正常发布；改成真实地址只影响本地 `hugo server` 的预览路径和 RSS 里的绝对链接。
站内链接都用相对站点根的路径生成，项目页（带 `/ai-radar/` 子路径）和自定义域名都能用。

## 注意

- `content/reports/*/index.html` 是生成物，改内容请改 `reports-src/` 或原始 Markdown 后重跑脚本。
- 正文是 HTML 内容文件，`hugo.toml` 里的 `[security] allowContent` 必须保留 `text/html`。
- 字体（Google Fonts）和 mermaid（jsDelivr）走公共 CDN，个别网络环境下加载慢时正文仍可读，图表会延迟出现。
- 仓库公开后，`reports-src/` 里的原始 Markdown 也是公开的。
