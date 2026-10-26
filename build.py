"""Build README.md and the GitHub Pages site (docs/) from data/works.json.

data/works.json is a list of approved, tagged works exported from 镜鉴. Each work:
  id, title, title_en, desc, desc_en, creator, handle, platform, url, model, prompt, promptSource,
  likes, views, postedAt, orientation, addedAt, tags {画风: [...], 地域氛围: [...], ...}
Covers live at docs/covers/<id>.jpg.

Run: python3 build.py
"""
import datetime, html, json, pathlib, shutil

ROOT = pathlib.Path(__file__).parent
DOCS = ROOT / "docs"
BASE = "https://daiyixiang666.github.io/awesome-ai-video-prompts/"
REPO = "https://github.com/daiyixiang666/awesome-ai-video-prompts"
NAME = "镜鉴 · Awesome AI Video Prompts"
CONTACT = "yixiang@umich.edu"
TAGLINE_ZH = "人工精选的顶级 AI 影像与提示词，按画风、氛围、题材检索"
TAGLINE_EN = "Hand-picked top-tier AI videos with prompts — Seedance, Veo, Kling, Sora"
DIM_ORDER = ["画风", "地域氛围", "题材", "情绪", "镜头技法", "用途"]

works = json.loads((ROOT / "data/works.json").read_text())
tax_en = json.loads((ROOT / "data/taxonomy_en.json").read_text())
works.sort(key=lambda w: (w.get("addedAt", ""), w.get("likes", 0)), reverse=True)
today = datetime.date.today().isoformat()
e = html.escape


def val_en(v):
    return tax_en["values"].get(v, [v, v])


def dim_en(d):
    return tax_en["dims"][d]


def tag_path(d, v):
    return f"t/{dim_en(d)[0]}/{val_en(v)[0]}.html"


def fmt(n):
    n = int(n or 0)
    if n >= 10**8: return f"{n / 10**8:.1f}亿".replace(".0亿", "亿")
    if n >= 10**4: return f"{n / 10**4:.1f}万".replace(".0万", "万")
    return str(n)


def tag_index():
    idx = {}
    for w in works:
        for d in DIM_ORDER:
            for v in w.get("tags", {}).get(d, []):
                idx.setdefault((d, v), []).append(w)
    return idx


# ---------- HTML ----------

def page(title, desc, path, body, jsonld=None, cover=None):
    url = BASE + path
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ""
    og_img = f'<meta property="og:image" content="{BASE}{cover}">' if cover else ""
    depth = path.count("/")
    root = "../" * depth
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website"><meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{url}">{og_img}
<meta name="twitter:card" content="summary_large_image">
<link rel="alternate" type="application/json" href="{BASE}works.json" title="All works (JSON)">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@700;900&family=Noto+Sans+SC:wght@400;500&family=JetBrains+Mono&display=swap">
<link rel="stylesheet" href="{root}style.css">{ld}
</head><body>
<header><div class="wrap top"><a class="brand" href="{root}index.html"><b>镜<i>鉴</i></b><span>Awesome AI Video Prompts</span></a>
<nav><a href="{root}index.html">作品 Works</a><a href="{root}tags.html">标签 Tags</a><a href="{REPO}">GitHub</a></nav></div></header>
<main class="wrap">{body}</main>
<footer class="wrap"><p>作品版权归原作者所有，本站只做索引、标注与提示词整理，并链接到原帖。如权利人认为收录不当，请发邮件至 <a href="mailto:{CONTACT}">{CONTACT}</a>（或在 <a href="{REPO}/issues">GitHub Issues</a> 留言），我们核实后第一时间下架。<br>
All works belong to their creators; this site only indexes and annotates them and links to the original posts. If you are a rights holder and want a work removed, email <a href="mailto:{CONTACT}">{CONTACT}</a> (or open a GitHub issue) and we will take it down promptly.</p>
<p>Machine-readable: <a href="{root}works.json">works.json</a> · <a href="{root}llms.txt">llms.txt</a> · <a href="{root}sitemap.xml">sitemap.xml</a></p></footer>
</body></html>"""


def card(w, root):
    tags = [v for d in ["画风", "地域氛围", "题材"] for v in w.get("tags", {}).get(d, [])[:2] if v != "无明显地域"][:4]
    return f"""<a class="card" href="{root}w/{w['id']}.html">
<figure><img src="{root}covers/{w['id']}.jpg" alt="{e(w['title'])} — AI video by {e(w['creator'])}" loading="lazy">
<span class="plat">{e(w['platform'])}</span>{'<span class="hp">附提示词 Prompt</span>' if w.get('prompt') else ''}</figure>
<div class="cb"><h3>{e(w['title'])}</h3><p class="by">{e(w['creator'])}{' · ' + e(w['model']) if w.get('model') else ''}</p>
<p class="tg">{' '.join(f'<span>{e(t)}</span>' for t in tags)}</p></div></a>"""


def grid(ws, root):
    return '<div class="grid">' + "".join(card(w, root) for w in ws) + "</div>" if ws else \
        '<p class="empty">首批作品正在人工筛选中，很快上线。 The first hand-picked batch is being reviewed.</p>'


def build_index(idx):
    chips = "".join(
        f'<a class="chip" href="{tag_path(d, v)}">{e(v)} <small>{len(ws)}</small></a>'
        for (d, v), ws in sorted(idx.items(), key=lambda kv: -len(kv[1]))[:24])
    body = f"""<section class="hero"><h1>镜鉴 · Awesome AI Video Prompts</h1>
<p>{TAGLINE_ZH}。<br>{TAGLINE_EN}.</p>
<p class="meta">{len(works)} 部作品 works · {sum(1 for w in works if w.get('prompt'))} 附完整提示词 with prompts · 更新于 updated {today}</p>
{f'<div class="chips">{chips}</div>' if chips else ''}</section>
{grid(works, '')}"""
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": NAME, "url": BASE,
          "description": f"{TAGLINE_ZH}. {TAGLINE_EN}.", "inLanguage": ["zh-CN", "en"],
          "hasPart": [{"@type": "CreativeWork", "name": w["title"], "url": f"{BASE}w/{w['id']}.html"} for w in works[:100]]}
    return page(f"{NAME} — 顶级 AI 视频提示词合集", f"{TAGLINE_ZH}。{TAGLINE_EN}.", "index.html", body, ld)


def build_work(w):
    root = "../"
    t_en = w.get("title_en") or ""
    rows = [("作者 Creator", f'<a href="{e(w["url"])}" rel="nofollow noopener">{e(w["creator"])} {e(w.get("handle", ""))}</a>'),
            ("平台 Platform", e(w["platform"])), ("模型 Model", e(w.get("model") or "—")),
            ("点赞 Likes", fmt(w.get("likes"))), ("发布 Posted", e(str(w.get("postedAt", ""))[:10]))]
    tagrows = "".join(
        f'<tr><th>{d} <small>{dim_en(d)[1]}</small></th><td>' +
        " ".join(f'<a class="chip" href="{root}{tag_path(d, v)}">{e(v)} <small>{e(val_en(v)[1])}</small></a>' for v in w["tags"][d]) +
        "</td></tr>" for d in DIM_ORDER if w.get("tags", {}).get(d))
    prompt = (f'<h2>提示词 Prompt{" · 来自" + e(w["promptSource"]) if w.get("promptSource") else ""}</h2><pre class="prompt">{e(w["prompt"])}</pre>'
              if w.get("prompt") else '<p class="muted">作者没有公开提示词。 The creator has not published the prompt.</p>')
    body = f"""<article class="work"><figure class="hero-img"><img src="{root}covers/{w['id']}.jpg" alt="{e(w['title'])} — AI video still"></figure>
<div class="info"><h1>{e(w['title'])}{f' <small>{e(t_en)}</small>' if t_en else ''}</h1>
<p>{e(w.get('desc', ''))}</p>{f"<p class='muted'>{e(w['desc_en'])}</p>" if w.get('desc_en') else ''}
<p><a class="btn" href="{e(w['url'])}" rel="nofollow noopener">观看原作 Watch on {e(w['platform'])} ↗</a></p>
<table class="kv">{''.join(f'<tr><th>{k}</th><td>{v}</td></tr>' for k, v in rows)}{tagrows}</table>
{prompt}</div></article>"""
    tags_flat = [v for d in DIM_ORDER for v in w.get("tags", {}).get(d, [])]
    ld = {"@context": "https://schema.org", "@type": "CreativeWork", "name": w["title"], "alternateName": t_en or None,
          "description": w.get("desc", ""), "url": f"{BASE}w/{w['id']}.html", "sameAs": w["url"],
          "image": f"{BASE}covers/{w['id']}.jpg", "dateCreated": w.get("postedAt"),
          "author": {"@type": "Person", "name": w["creator"], "url": w["url"]},
          "keywords": ", ".join(tags_flat + [val_en(v)[1] for v in tags_flat] + ([w["model"]] if w.get("model") else [])),
          "genre": tags_flat, "isAccessibleForFree": True}
    if w.get("prompt"): ld["text"] = w["prompt"]
    ld = {k: v for k, v in ld.items() if v}
    model = f" {w['model']}" if w.get("model") else ""
    title = f"{w['title']} — {w['creator']}{model} AI 视频" + (" 提示词 Prompt" if w.get("prompt") else "")
    desc = f"{w.get('desc', '')} 标签：{'、'.join(tags_flat[:6])}。" + (" 附完整提示词。" if w.get("prompt") else "")
    return page(title, desc, f"w/{w['id']}.html", body, ld, cover=f"covers/{w['id']}.jpg")


def build_tag(d, v, ws):
    en = val_en(v)[1]
    root = "../../"
    with_p = sum(1 for w in ws if w.get("prompt"))
    body = f"""<section class="hero"><p class="crumb"><a href="{root}tags.html">标签</a> / {d}</p>
<h1>{e(v)} AI 视频 <small>{e(en)} AI videos</small></h1>
<p>{len(ws)} 部人工精选的「{e(v)}」风格 AI 视频作品，{with_p} 部附完整提示词，涵盖 Seedance、Veo、Kling、Sora 等模型。<br>
{len(ws)} hand-picked {e(en.lower())} AI videos, {with_p} with full prompts.</p></section>{grid(ws, root)}"""
    return page(f"{v} AI 视频提示词 · {en} AI video prompts — 镜鉴", f"人工精选的{v}风格顶级 AI 视频与提示词。Hand-picked {en} AI videos with prompts.",
                tag_path(d, v), body)


def build_tags(idx):
    secs = ""
    for d in DIM_ORDER:
        items = [(v, ws) for (dd, v), ws in idx.items() if dd == d]
        if not items: continue
        secs += f"<h2>{d} <small>{dim_en(d)[1]}</small></h2><div class='chips'>" + "".join(
            f'<a class="chip" href="{tag_path(d, v)}">{e(v)} <small>{e(val_en(v)[1])} · {len(ws)}</small></a>' for v, ws in sorted(items, key=lambda x: -len(x[1]))) + "</div>"
    body = f"<section class='hero'><h1>全部标签 <small>All tags</small></h1></section>{secs or grid([], '')}"
    return page("全部标签 All tags — 镜鉴 Awesome AI Video Prompts", "按画风、地域氛围、题材、情绪、镜头技法、用途检索 AI 视频。", "tags.html", body)


# ---------- machine-readable ----------

def public_record(w):
    keep = ["id", "title", "title_en", "desc", "desc_en", "creator", "handle", "platform", "url", "model",
            "prompt", "promptSource", "likes", "postedAt", "orientation", "tags"]
    r = {k: w[k] for k in keep if w.get(k) not in (None, "", [], {})}
    r["page"] = f"{BASE}w/{w['id']}.html"; r["cover"] = f"{BASE}covers/{w['id']}.jpg"
    r["tags_en"] = {dim_en(d)[0]: [val_en(v)[0] for v in vs] for d, vs in w.get("tags", {}).items() if d in tax_en["dims"]}
    return r


def llms_txt(idx):
    lines = [f"# {NAME}", "", f"> {TAGLINE_EN}. {TAGLINE_ZH}。", "",
             "A human-curated index of top-tier AI-generated videos from X, TikTok and Douyin. Every entry is reviewed by a person, "
             "tagged on six facets (visual style, regional vibe, genre, mood, camera technique, use case), credits the original creator, "
             "and includes the full generation prompt whenever the creator published it. Models covered include Seedance, Veo, Kling, Sora and Midjourney.",
             "", "## Data", f"- [works.json]({BASE}works.json): every work as JSON (prompt, tags in Chinese and English slugs, creator, source URL, model)",
             f"- [All tags]({BASE}tags.html)", f"- [GitHub repository]({REPO})", "",
             f"Takedown / contact: {CONTACT} — works are removed promptly at the rights holder's request.", "", "## Works with prompts"]
    for w in [w for w in works if w.get("prompt")][:200]:
        lines.append(f"- [{w['title']}{' / ' + w['title_en'] if w.get('title_en') else ''}]({BASE}w/{w['id']}.html): {w.get('model') or 'AI video'} by {w['creator']}")
    lines += ["", "## Tags"]
    for (d, v), ws in sorted(idx.items(), key=lambda kv: -len(kv[1])):
        lines.append(f"- [{v} / {val_en(v)[1]}]({BASE}{tag_path(d, v)}): {len(ws)} works")
    return "\n".join(lines) + "\n"


def readme(idx):
    by_style = {}
    for w in works:
        s = (w.get("tags", {}).get("画风") or ["其他"])[0]
        by_style.setdefault(s, []).append(w)
    out = [f"# 镜鉴 · Awesome AI Video Prompts", "",
           f"> {TAGLINE_ZH}。  ", f"> {TAGLINE_EN}.", "",
           f"**[在线浏览 Browse online →]({BASE})** · {len(works)} works · {sum(1 for w in works if w.get('prompt'))} with full prompts · updated {today}", "",
           "每一部作品都经过人工筛选，来自 X、TikTok、抖音的顶级 AI 影像创作者；按 **画风 / 地域氛围 / 题材 / 情绪 / 镜头技法 / 用途** 六个维度打标，并尽可能附上作者公开的完整提示词。",
           "", "Every entry is hand-picked from top AI filmmakers on X, TikTok and Douyin, tagged on six facets, credited to its creator, and includes the full prompt whenever it was published.", ""]
    if not works:
        out += ["_首批作品正在筛选中 — the first batch is under review._", ""]
    out += ["## 目录 Contents", ""] + [f"- [{s} {val_en(s)[1]}](#{val_en(s)[0]}) ({len(ws)})" for s, ws in by_style.items()] + [""]
    for s, ws in by_style.items():
        out += [f'<a id="{val_en(s)[0]}"></a>', f"## {s} · {val_en(s)[1]}", ""]
        for w in ws:
            tags = " ".join(f"`{v}`" for d in DIM_ORDER for v in w.get("tags", {}).get(d, []))
            out += [f"### [{w['title']}{' · ' + w['title_en'] if w.get('title_en') else ''}]({BASE}w/{w['id']}.html)", "",
                    f'<a href="{BASE}w/{w["id"]}.html"><img src="docs/covers/{w["id"]}.jpg" width="420" alt="{e(w["title"])}"></a>', "",
                    f"- **作者 Creator:** [{w['creator']}]({w['url']}) · {w['platform']}" + (f" · **{w['model']}**" if w.get("model") else "") + f" · ♥ {fmt(w.get('likes'))}",
                    f"- **标签 Tags:** {tags}", f"- {w.get('desc', '')}", ""]
            if w.get("prompt"):
                out += ["<details><summary>提示词 Prompt</summary>", "", "```text", w["prompt"], "```", "", "</details>", ""]
    out += ["## 收录标准 Curation", "", "- 只收顶级：审美、叙事或技术上有明显过人之处；不收梗图、软色情、搬运。",
            "- Original creators are always credited and linked. 版权归原作者。", "",
            "## 版权与下架 Takedown", "",
            f"如权利人认为收录不当，请发邮件至 **{CONTACT}** 或提 Issue，我们核实后第一时间下架。  ",
            f"Rights holders: email **{CONTACT}** or open an issue and we will remove the work promptly.", "",
            "## 机器可读 Machine-readable", "", f"- [`works.json`]({BASE}works.json) · [`llms.txt`]({BASE}llms.txt) · [`sitemap.xml`]({BASE}sitemap.xml)", ""]
    return "\n".join(out)


def sitemap(paths):
    return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(
        f"  <url><loc>{BASE}{p}</loc><lastmod>{today}</lastmod></url>\n" for p in paths) + "</urlset>\n"


ROBOTS = f"""User-agent: *
Allow: /

User-agent: GPTBot
Allow: /
User-agent: OAI-SearchBot
Allow: /
User-agent: ChatGPT-User
Allow: /
User-agent: ClaudeBot
Allow: /
User-agent: Claude-SearchBot
Allow: /
User-agent: PerplexityBot
Allow: /
User-agent: Google-Extended
Allow: /
User-agent: Bytespider
Allow: /

Sitemap: {BASE}sitemap.xml
"""


def main():
    for sub in ["w", "t"]:
        shutil.rmtree(DOCS / sub, ignore_errors=True)
    DOCS.mkdir(exist_ok=True)
    idx = tag_index()
    files = {"index.html": build_index(idx), "tags.html": build_tags(idx)}
    for w in works:
        files[f"w/{w['id']}.html"] = build_work(w)
    for (d, v), ws in idx.items():
        files[tag_path(d, v)] = build_tag(d, v, ws)
    for p, s in files.items():
        f = DOCS / p; f.parent.mkdir(parents=True, exist_ok=True); f.write_text(s)
    (DOCS / "works.json").write_text(json.dumps([public_record(w) for w in works], ensure_ascii=False, indent=1))
    (DOCS / "llms.txt").write_text(llms_txt(idx))
    (DOCS / "sitemap.xml").write_text(sitemap(list(files)))
    (DOCS / "robots.txt").write_text(ROBOTS)
    (DOCS / ".nojekyll").write_text("")
    (ROOT / "README.md").write_text(readme(idx))
    print(f"{len(works)} works, {len(idx)} tag pages, {len(files)} html files")


if __name__ == "__main__":
    main()
