"""Build README.md / README.en.md and the bilingual GitHub Pages site (docs/) from data/works.json.

data/works.json is a list of approved, tagged works exported from 镜鉴. Each work:
  id, title, title_en, desc, desc_en, creator, handle, platform, url, model, prompt, promptSource,
  likes, views, postedAt, orientation, duration, addedAt, tags {画风: [...], 地域氛围: [...], ...}
Covers live at docs/covers/<id>.jpg (shared by both languages).

Chinese pages live at the site root, English pages under /en/, with hreflang alternates and a switcher.
Run: python3 build.py
"""
import datetime, html, json, pathlib, shutil

ROOT = pathlib.Path(__file__).parent
DOCS = ROOT / "docs"
BASE = "https://daiyixiang666.github.io/awesome-ai-video-prompts/"
REPO = "https://github.com/daiyixiang666/awesome-ai-video-prompts"
CONTACT = "yixiang@umich.edu"
DIM_ORDER = ["画风", "地域氛围", "题材", "情绪", "镜头技法", "用途"]
LANGS = {"zh": "", "en": "en/"}

T = {
    "zh": {
        "html_lang": "zh-CN", "switch": "English", "name": "镜鉴 · 顶级 AI 视频提示词",
        "tagline": "人工精选的顶级 AI 视频、图片与 Coding 作品，附提示词，按画风、氛围、题材检索",
        "med": {"video": "视频", "image": "图片", "web": "Coding"},
        "med_p": {"video": "AI 视频生成模型（Seedance、Kling、Veo…）生成的单条短片。", "image": "图片生成模型（Midjourney、GPT Image、Nano Banana…）生成的作品。", "web": "大语言模型写代码做出的作品（three.js、WebGL、shader…），包括用代码渲染的视频。"},
        "live": "打开在线作品", "repo": "源码", "made_with": "AI 工具", "stack": "技术栈",
        "nav_works": "作品", "nav_tags": "标签", "works": "部作品", "with_prompts": "附完整提示词", "updated": "更新于",
        "has_prompt": "附提示词", "empty": "首批作品正在人工筛选中，很快上线。",
        "creator": "作者", "platform": "平台", "model": "模型", "likes": "点赞", "posted": "发布", "duration": "时长",
        "watch": "观看原作", "prompt": "提示词", "prompt_from": "来自", "no_prompt": "作者没有公开提示词。",
        "all_tags": "全部标签", "tags_desc": "按画风、地域氛围、题材、情绪、镜头技法、用途检索 AI 视频。",
        "tag_h1": "{v} AI 视频", "tag_p": "{n} 部人工精选的「{v}」AI 视频，{p} 部附完整提示词，涵盖 Seedance、Veo、Kling、Sora 等模型。",
        "tag_title": "{v} AI 视频提示词 — 镜鉴", "tag_desc": "人工精选的{v}风格顶级 AI 视频与提示词。",
        "work_title": "{t} — {c}{m} AI 视频{p}", "work_title_p": " 提示词", "tags_word": "标签",
        "footer": "作品版权归原作者所有，本站只做索引、标注与提示词整理，并链接到原帖。如权利人认为收录不当，请发邮件至 {mail}（或在 {issues} 留言），我们核实后第一时间下架。",
        "machine": "机器可读", "home_title": "镜鉴 — 顶级 AI 视频提示词合集",
        "submit": "投稿", "submit_desc": "推荐一部 AI 视频、图片或 Coding 作品到镜鉴，自己的或别人的都可以。",
        "submit_body": """<p>看到好作品，或者自己做了得意的作品，都欢迎推荐。每部投稿都会人工筛选，入选后署名并链接原作者。</p>
<h2>收什么</h2><ul><li><b>视频</b>：AI 视频模型生成的单条短片，60 秒以内（短片加制作讲解也可以）。</li>
<li><b>图片</b>：AI 图片模型生成的作品，偏好有艺术感的。</li><li><b>Coding</b>：大模型写代码做出的作品（three.js、WebGL、shader…），需写明用的 AI 工具。</li></ul>
<h2>不收什么</h2><p>搬运、广告、梗图、擦边，以及看不出审美和方法的作品。</p>
<h2>怎么投</h2><p class="btns"><a class="btn" href="{form}">用 GitHub 投稿</a></p>
<p>没有 GitHub 账号？把原作链接、作者、用的模型（和公开的提示词，如有）发邮件到 {mail}。</p>""",
    },
    "en": {
        "html_lang": "en", "switch": "中文", "name": "Jingjian · Awesome AI Video Prompts",
        "tagline": "Hand-picked top-tier AI videos, images and AI-coded works with their prompts — searchable by style, mood and genre",
        "med": {"video": "Video", "image": "Images", "web": "Coding"},
        "med_p": {"video": "Single short clips from AI video models (Seedance, Kling, Veo…).", "image": "Work from AI image models (Midjourney, GPT Image, Nano Banana…).", "web": "Works an LLM built by writing code (three.js, WebGL, shaders…), including code-rendered videos."},
        "live": "Open live demo", "repo": "Source", "made_with": "Built with", "stack": "Stack",
        "nav_works": "Works", "nav_tags": "Tags", "works": "works", "with_prompts": "with full prompts", "updated": "updated",
        "has_prompt": "Prompt", "empty": "The first hand-picked batch is being reviewed and will be up soon.",
        "creator": "Creator", "platform": "Platform", "model": "Model", "likes": "Likes", "posted": "Posted", "duration": "Length",
        "watch": "Watch on", "prompt": "Prompt", "prompt_from": "from the", "no_prompt": "The creator has not published the prompt.",
        "all_tags": "All tags", "tags_desc": "Browse AI videos by visual style, regional vibe, genre, mood, camera technique and use case.",
        "tag_h1": "{v} AI videos", "tag_p": "{n} hand-picked {v_l} AI videos, {p} with full prompts — Seedance, Veo, Kling, Sora and more.",
        "tag_title": "{v} AI video prompts — Jingjian", "tag_desc": "Hand-picked {v_l} AI videos with their prompts.",
        "work_title": "{t} — {c}{m} AI video{p}", "work_title_p": " prompt", "tags_word": "Tags",
        "footer": "All works belong to their creators; this site only indexes and annotates them and links to the original posts. Rights holders who want a work removed can email {mail} (or open a {issues}) and we will take it down promptly.",
        "machine": "Machine-readable", "home_title": "Jingjian — Awesome AI Video Prompts",
        "submit": "Submit", "submit_desc": "Recommend an AI video, image or AI-coded work for Jingjian — yours or someone else's.",
        "submit_body": """<p>Found a great piece, or made one you are proud of? Recommend it. Every submission is screened by hand; selected works credit and link the original creator.</p>
<h2>What we take</h2><ul><li><b>Video</b>: single clips from AI video models, up to 60 s (a clip plus a how-it-was-made breakdown is fine).</li>
<li><b>Images</b>: work from AI image models, artistic work preferred.</li><li><b>Coding</b>: works an LLM built by writing code (three.js, WebGL, shaders…); name the AI tool.</li></ul>
<h2>What we don't</h2><p>Re-uploads, ads, memes, sexual bait, and work without clear taste or craft.</p>
<h2>How to submit</h2><p class="btns"><a class="btn" href="{form}">Submit on GitHub</a></p>
<p>No GitHub account? Email the link to the original post, the creator, the model (and the prompt, if published) to {mail}.</p>""",
    },
}
SRC_EN = {"正文": "post", "作者评论": "author's reply"}

works = json.loads((ROOT / "data/works.json").read_text())
tax_en = json.loads((ROOT / "data/taxonomy_en.json").read_text())
works.sort(key=lambda w: (w.get("addedAt", ""), w.get("likes", 0)), reverse=True)
today = datetime.date.today().isoformat()
e = html.escape


MED_ORDER = ["video", "image", "web"]
MED_PAGE = {"video": "index.html", "image": "images.html", "web": "coding.html"}
MED_NOUN = {"video": "AI video", "image": "AI image", "web": "AI-coded work"}


def med(w):
    return w.get("medium") or "video"


def val_en(v):
    return tax_en["values"].get(v, [v, v])


def dim_en(d):
    return tax_en["dims"][d]


def lab(v, lang):
    return v if lang == "zh" else val_en(v)[1]


def dlab(d, lang):
    return d if lang == "zh" else dim_en(d)[1]


MED_SLUG = {"video": "video", "image": "images", "web": "coding"}


def tag_path(d, v, m=None):
    """All-section tag page, or with m the tag page limited to one section (视频 / 图片 / Coding)."""
    return f"t/{MED_SLUG[m]}/{dim_en(d)[0]}/{val_en(v)[0]}.html" if m else f"t/{dim_en(d)[0]}/{val_en(v)[0]}.html"


def title(w, lang):
    return w["title"] if lang == "zh" else (w.get("title_en") or w["title"])


def desc(w, lang):
    return w.get("desc", "") if lang == "zh" else (w.get("desc_en") or w.get("desc", ""))


def fmt(n, lang):
    n = int(n or 0)
    if lang == "en":
        return f"{n / 1e6:.1f}M".replace(".0M", "M") if n >= 1e6 else f"{n / 1e3:.1f}K".replace(".0K", "K") if n >= 1e3 else str(n)
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

def page(lang, path, title_, desc_, body, jsonld=None, cover=None):
    s = T[lang]
    url = BASE + LANGS[lang] + path
    root = "../" * (LANGS[lang] + path).count("/")
    other = "en" if lang == "zh" else "zh"
    other_href = root + LANGS[other] + path
    alts = "".join(f'<link rel="alternate" hreflang="{T[l]["html_lang"]}" href="{BASE}{LANGS[l]}{path}">' for l in LANGS)
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ""
    og_img = f'<meta property="og:image" content="{BASE}{cover}">' if cover else ""
    mail = f'<a href="mailto:{CONTACT}">{CONTACT}</a>'
    issues = f'<a href="{REPO}/issues">GitHub {"Issues" if lang == "zh" else "issue"}</a>'
    return f"""<!doctype html>
<html lang="{s['html_lang']}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title_)}</title>
<meta name="description" content="{e(desc_)}">
<link rel="canonical" href="{url}">{alts}<link rel="alternate" hreflang="x-default" href="{BASE}{path}">
<meta property="og:type" content="website"><meta property="og:title" content="{e(title_)}">
<meta property="og:description" content="{e(desc_)}"><meta property="og:url" content="{url}">{og_img}
<meta name="twitter:card" content="summary_large_image">
<link rel="alternate" type="application/json" href="{BASE}works.json" title="All works (JSON)">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@700;900&family=Noto+Sans+SC:wght@400;500&family=JetBrains+Mono&display=swap">
<link rel="stylesheet" href="{root}style.css">{ld}
</head><body>
<header><div class="wrap top"><a class="brand" href="{root}{LANGS[lang]}index.html"><b>镜<i>鉴</i></b><span>Awesome AI Video Prompts</span></a>
<nav>{''.join(f'<a href="{root}{LANGS[lang]}{MED_PAGE[m]}">{s["med"][m]}</a>' for m in MED_ORDER)}<a href="{root}{LANGS[lang]}tags.html">{s['nav_tags']}</a><a class="sub" href="{root}{LANGS[lang]}submit.html">{s['submit']}</a><a href="{REPO}">GitHub</a><a class="lang" href="{other_href}" hreflang="{T[other]['html_lang']}">{s['switch']}</a></nav></div></header>
<main class="wrap">{body}</main>
<footer class="wrap"><p>{s['footer'].format(mail=mail, issues=issues)}</p>
<p>{s['machine']}: <a href="{root}works.json">works.json</a> · <a href="{root}llms.txt">llms.txt</a> · <a href="{root}sitemap.xml">sitemap.xml</a></p></footer>
</body></html>"""


def card(w, lang, root):
    s = T[lang]
    tags = [lab(v, lang) for d in ["画风", "地域氛围", "题材"] for v in w.get("tags", {}).get(d, [])[:2] if v != "无明显地域"][:4]
    t = title(w, lang)
    return f"""<a class="card" href="{root}{LANGS[lang]}w/{w['id']}.html">
<figure><img src="{root}covers/{w['id']}.jpg" alt="{e(t)} — {MED_NOUN[med(w)]} by {e(w['creator'])}" loading="lazy">
<span class="plat">{e(w['platform'])}</span>{f'<span class="nimg">{len(w["images"]) + 1}</span>' if w.get("images") else ''}{f'<span class="hp">{s["has_prompt"]}</span>' if w.get('prompt') else ''}</figure>
<div class="cb"><h3>{e(t)}</h3><p class="by">{e(w['creator'])}{' · ' + e(w.get('made_with') or w.get('model')) if (w.get('made_with') or w.get('model')) else ''}</p>
<p class="tg">{' '.join(f'<span>{e(x)}</span>' for x in tags)}</p></div></a>"""


def grid(ws, lang, root):
    return '<div class="grid">' + "".join(card(w, lang, root) for w in ws) + "</div>" if ws else f'<p class="empty">{T[lang]["empty"]}</p>'


def build_index(lang, idx, m="video"):
    s, root = T[lang], "../" * LANGS[lang].count("/")
    ws_m = [w for w in works if med(w) == m]
    idx = {k: [w for w in v if med(w) == m] for k, v in idx.items()}
    idx = {k: v for k, v in idx.items() if v}
    tabs = "".join(f'<a class="tab{" on" if x == m else ""}" href="{MED_PAGE[x]}">{s["med"][x]} <small>{sum(1 for w in works if med(w) == x)}</small></a>' for x in MED_ORDER)
    chips = "".join(f'<a class="chip" href="{tag_path(d, v, m)}">{e(lab(v, lang))} <small>{len(ws)}</small></a>'
                    for (d, v), ws in sorted(idx.items(), key=lambda kv: -len(kv[1]))[:24])
    n_p = sum(1 for w in works if w.get("prompt"))
    body = f"""<section class="hero"><h1>{s['name']}</h1><p>{s['tagline']}.</p>
<p class="meta">{len(works)} {s['works']} · {n_p} {s['with_prompts']} · {s['updated']} {today}</p>
<nav class="tabs">{tabs}</nav><p class="medp">{s['med_p'][m]}</p>
{f'<div class="chips">{chips}</div>' if chips else ''}</section>{grid(ws_m, lang, root)}"""
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": s["name"], "url": BASE + LANGS[lang],
          "description": s["tagline"], "inLanguage": s["html_lang"],
          "hasPart": [{"@type": "CreativeWork", "name": title(w, lang), "url": f"{BASE}{LANGS[lang]}w/{w['id']}.html"} for w in ws_m[:100]]}
    ttl = s["home_title"] if m == "video" else f'{s["med"][m]} — {s["name"]}'
    return page(lang, MED_PAGE[m], ttl, s["med_p"][m] if m != "video" else s["tagline"], body, ld)


def build_work(w, lang):
    s, root = T[lang], "../" * (LANGS[lang].count("/") + 1)
    t, dsc = title(w, lang), desc(w, lang)
    rows = [(s["creator"], f'<a href="{e(w["url"])}" rel="nofollow noopener">{e(w["creator"])} {e(w.get("handle", ""))}</a>'),
            (s["platform"], e(w["platform"]))]
    rows += [(s["made_with"], e(w["made_with"]))] if w.get("made_with") else [(s["model"], e(w.get("model") or "—"))]
    rows += [(s["stack"], e(" · ".join(w["stack"])))] if w.get("stack") else []
    rows += [
            (s["duration"], f'{round(w["duration"])}s' if w.get("duration") else "—"),
            (s["likes"], fmt(w.get("likes"), lang)), (s["posted"], e(str(w.get("postedAt", ""))[:10]))]
    if med(w) == "image": rows = [r for r in rows if r[0] != s["duration"]]
    tagrows = "".join(
        f'<tr><th>{dlab(d, lang)}</th><td>' + " ".join(f'<a class="chip" href="{root}{LANGS[lang]}{tag_path(d, v, med(w))}">{e(lab(v, lang))}</a>' for v in w["tags"][d]) + "</td></tr>"
        for d in DIM_ORDER if w.get("tags", {}).get(d))
    src = w.get("promptSource", "")
    src = (f" · {s['prompt_from']}{src}" if lang == "zh" else f" · {s['prompt_from']} {SRC_EN.get(src, src)}") if src else ""
    prompt = f'<h2>{s["prompt"]}{e(src)}</h2><pre class="prompt">{e(w["prompt"])}</pre>' if w.get("prompt") else f'<p class="muted">{s["no_prompt"]}</p>'
    if med(w) == "image":
        imgs = [f"{root}covers/{w['id']}.jpg"] + [f"{root}img/{x}" for x in w.get("images", [])]
        media = '<div class="gal">' + "".join(f'<img src="{x}" alt="{e(t)} — {MED_NOUN["image"]} {k + 1}" loading="lazy">' for k, x in enumerate(imgs)) + "</div>"
    else: media = (f'<video src="{e(w["video_url"])}" poster="{root}covers/{w["id"]}.jpg" controls playsinline loop muted autoplay preload="metadata"></video>'
             if w.get("video_url") else f'<img src="{root}covers/{w["id"]}.jpg" alt="{e(t)} — AI video still">')
    body = f"""<article class="work"><figure class="hero-img">{media}</figure>
<div class="info"><h1>{e(t)}</h1><p>{e(dsc)}</p>
<p class="btns"><a class="btn" href="{e(w['url'])}" rel="nofollow noopener">{s['watch']} {e(w['platform'])} ↗</a>{f'<a class="btn" href="{e(w["live_url"])}" rel="nofollow noopener">{s["live"]} ↗</a>' if w.get("live_url") else ''}{f'<a class="btn" href="{e(w["repo_url"])}" rel="nofollow noopener">{s["repo"]} ↗</a>' if w.get("repo_url") else ''}</p>
<table class="kv">{''.join(f'<tr><th>{k}</th><td>{v}</td></tr>' for k, v in rows)}{tagrows}</table>{prompt}</div></article>"""
    tags_flat = [lab(v, lang) for d in DIM_ORDER for v in w.get("tags", {}).get(d, [])]
    ld = {"@context": "https://schema.org", "@type": "VideoObject" if w.get("video_url") else "CreativeWork", "name": t, "description": dsc or t, "inLanguage": s["html_lang"],
          "contentUrl": w.get("video_url"), "thumbnailUrl": f"{BASE}covers/{w['id']}.jpg" if w.get("video_url") else None,
          "uploadDate": w.get("postedAt") if w.get("video_url") else None, "duration": f"PT{round(w['duration'])}S" if w.get("duration") else None,
          "url": f"{BASE}{LANGS[lang]}w/{w['id']}.html", "sameAs": w["url"], "image": f"{BASE}covers/{w['id']}.jpg",
          "dateCreated": w.get("postedAt"), "author": {"@type": "Person", "name": w["creator"], "url": w["url"]},
          "keywords": ", ".join(tags_flat + [x for x in [w.get("model"), w.get("made_with")] + w.get("stack", []) if x]), "genre": tags_flat, "isAccessibleForFree": True}
    if w.get("prompt"): ld["text"] = w["prompt"]
    ld = {k: v for k, v in ld.items() if v}
    m = f" {w['model']}" if w.get("model") else ""
    ttl = s["work_title"].format(t=t, c=w["creator"], m=m, p=s["work_title_p"] if w.get("prompt") else "")
    if med(w) != "video": ttl = ttl.replace("AI 视频", "AI 图片" if med(w) == "image" else "AI Coding").replace("AI video", MED_NOUN[med(w)])
    sep = "、" if lang == "zh" else ", "
    d_ = f"{dsc} {s['tags_word']}: {sep.join(tags_flat[:6])}."
    return page(lang, f"w/{w['id']}.html", ttl, d_, body, ld, cover=f"covers/{w['id']}.jpg")


def build_tag(d, v, ws, lang):
    s, root = T[lang], "../" * (LANGS[lang].count("/") + 2)
    vl = lab(v, lang)
    p = sum(1 for w in ws if w.get("prompt"))
    body = f"""<section class="hero"><p class="crumb"><a href="{root}{LANGS[lang]}tags.html">{s['nav_tags']}</a> / {dlab(d, lang)}</p>
<h1>{s['tag_h1'].format(v=e(vl))}</h1><p>{s['tag_p'].format(n=len(ws), v=e(vl), v_l=e(vl.lower()), p=p)}</p></section>""" + "".join(
        f'<h2 class="medh">{s["med"][m]} <small>{len(g)}</small></h2>{grid(g, lang, root)}' for m in MED_ORDER for g in [[w for w in ws if med(w) == m]] if g)
    return page(lang, tag_path(d, v), s["tag_title"].format(v=vl), s["tag_desc"].format(v=vl, v_l=vl.lower()), body)


def build_tag_med(d, v, ws, lang, m):
    s, root = T[lang], "../" * (LANGS[lang].count("/") + 3)
    vl, ws_m = lab(v, lang), [w for w in ws if med(w) == m]
    tabs = "".join(f'<a class="tab{" on" if x == m else ""}" href="{root}{LANGS[lang]}{tag_path(d, v, x)}">{s["med"][x]} <small>{n}</small></a>'
                   for x in MED_ORDER for n in [sum(1 for w in ws if med(w) == x)] if n)
    p = sum(1 for w in ws_m if w.get("prompt"))
    h1 = f'{e(vl)} · {s["med"][m]}'
    body = f"""<section class="hero"><p class="crumb"><a href="{root}{LANGS[lang]}{MED_PAGE[m]}">{s['med'][m]}</a> / {dlab(d, lang)} / <a href="{root}{LANGS[lang]}{tag_path(d, v)}">{'全部分区' if lang == 'zh' else 'All sections'}</a></p>
<h1>{h1}</h1><p>{s['med_p'][m]}</p><nav class="tabs">{tabs}</nav></section>{grid(ws_m, lang, root)}"""
    return page(lang, tag_path(d, v, m), f'{vl} · {s["med"][m]} — {s["name"]}', f'{s["med_p"][m]} {vl}', body)


def build_tags(idx, lang):
    s = T[lang]
    secs = ""
    for d in DIM_ORDER:
        items = [(v, ws) for (dd, v), ws in idx.items() if dd == d]
        if not items: continue
        secs += f"<h2>{dlab(d, lang)}</h2><div class='chips'>" + "".join(
            f'<a class="chip" href="{tag_path(d, v)}">{e(lab(v, lang))} <small>{len(ws)}</small></a>' for v, ws in sorted(items, key=lambda x: -len(x[1]))) + "</div>"
    body = f"<section class='hero'><h1>{s['all_tags']}</h1><p>{s['tags_desc']}</p></section>{secs or grid([], lang, '')}"
    return page(lang, "tags.html", f"{s['all_tags']} — {s['name']}", s["tags_desc"], body)


SUBMIT_FORM = f"{REPO}/issues/new?template=submit.yml"


def build_submit(lang):
    s = T[lang]
    body = f"<section class='hero prose'><h1>{s['submit']}</h1>" + s["submit_body"].format(form=SUBMIT_FORM, mail=f'<a href="mailto:{CONTACT}">{CONTACT}</a>') + "</section>"
    return page(lang, "submit.html", f"{s['submit']} — {s['name']}", s["submit_desc"], body)


# ---------- machine-readable ----------

def public_record(w):
    keep = ["id", "title", "title_en", "desc", "desc_en", "creator", "handle", "platform", "url", "model",
            "prompt", "promptSource", "likes", "postedAt", "orientation", "duration", "video_url", "tags",
            "medium", "made_with", "stack", "live_url", "repo_url"]
    r = {k: w[k] for k in keep if w.get(k) not in (None, "", [], {})}
    r["page_zh"] = f"{BASE}w/{w['id']}.html"; r["page_en"] = f"{BASE}en/w/{w['id']}.html"; r["cover"] = f"{BASE}covers/{w['id']}.jpg"
    r["medium"] = med(w)
    if w.get("images"): r["images"] = [f"{BASE}img/{x}" for x in w["images"]]
    r["tags_en"] = {dim_en(d)[0]: [val_en(v)[0] for v in vs] for d, vs in w.get("tags", {}).items() if d in tax_en["dims"]}
    return r


def llms_txt(idx):
    lines = [f"# {T['en']['name']} (镜鉴)", "", f"> {T['en']['tagline']}. {T['zh']['tagline']}。", "",
             "A human-curated index of top-tier AI-generated short clips from X, TikTok and Douyin. Every entry is reviewed by a person, "
             "tagged on six facets (visual style, regional vibe, genre, mood, camera technique, use case), credits and links the original creator, "
             "and includes the full generation prompt whenever the creator published it. Models include Seedance, Veo, Kling, Sora and others. "
             f"English pages live under {BASE}en/, Chinese pages at {BASE}.", "",
             "## Data", f"- [works.json]({BASE}works.json): every work as JSON (prompt, Chinese + English tags, creator, source URL, model, both page URLs)",
             f"- [All tags (English)]({BASE}en/tags.html) · [全部标签 (中文)]({BASE}tags.html)", f"- [GitHub repository]({REPO})", "",
             f"Takedown / contact: {CONTACT} — works are removed promptly at the rights holder's request.", "", "## Works with prompts"]
    for w in [w for w in works if w.get("prompt")][:200]:
        lines.append(f"- [{title(w, 'en')}]({BASE}en/w/{w['id']}.html): {w.get('model') or 'AI video'} by {w['creator']}")
    lines += ["", "## Tags"]
    for (d, v), ws in sorted(idx.items(), key=lambda kv: -len(kv[1])):
        lines.append(f"- [{val_en(v)[1]} / {v}]({BASE}en/{tag_path(d, v)}): {len(ws)} works")
    return "\n".join(lines) + "\n"


def thumb(w):
    """Square 360px crop for the README grid, so portrait and landscape covers line up."""
    dst = DOCS / "thumbs" / f"{w['id']}.jpg"
    if not dst.exists():
        from PIL import Image, ImageOps
        dst.parent.mkdir(exist_ok=True)
        ImageOps.fit(Image.open(DOCS / "covers" / f"{w['id']}.jpg").convert("RGB"), (360, 360), Image.LANCZOS).save(dst, quality=82, optimize=True)
    return f"docs/thumbs/{w['id']}.jpg"


def readme(idx, lang):
    """Short landing README: badges, a cover grid of the newest works per section, tag shortcuts. The full list lives on the site."""
    zh, s = lang == "zh", T[lang]
    site = BASE + LANGS[lang]
    n_p = sum(1 for w in works if w.get("prompt"))
    badge = lambda l, m, c: f'<img alt="{l}" src="https://img.shields.io/badge/{l}-{m}-{c}?style=flat-square">'
    out = ['<div align="center">', "", f"# {s['name']}", "", f"**{s['tagline']}**", "",
           " · ".join([f"[{'在线浏览' if zh else 'Browse the site'}]({site})", f"[{s['nav_tags']}]({site}tags.html)",
                       f"[{s['submit']}]({SUBMIT_FORM})", "[English](README.en.md)" if zh else "[中文](README.md)", f"[works.json]({BASE}works.json)"]), "",
           " ".join([badge("works", len(works), "e2a24c"), badge("with_prompts", n_p, "2d2f33"), badge("updated", today.replace("-", "--"), "2d2f33")]),
           "", "</div>", "",
           ("人工筛选的 AI 作品合集，只收高审美、高方法论的作品，分 **视频**（≤60 秒短片）、**图片**、**Coding**（大模型写代码做的作品）三类。每部作品都署名并链接原作者，按画风、地域氛围、题材、情绪、镜头技法、用途打标，作者公开过提示词的附上完整提示词。"
            if zh else "A hand-picked collection of AI works with outstanding aesthetics and craft, in three sections: **Video** (clips ≤60 s), **Images** and **Coding** (works an LLM built by writing code). Every work credits and links its creator, is tagged by style, regional vibe, genre, mood, camera technique and use case, and includes the full prompt whenever the creator published it."), ""]
    for m in MED_ORDER:
        ws = [w for w in works if med(w) == m]
        if not ws: continue
        out += [f"## {s['med'][m]} <sup>{len(ws)}</sup>", "", f"{s['med_p'][m]} [{'查看全部' if zh else 'See all'} →]({site}{MED_PAGE[m]})", "", "<table>"]
        for r in range(0, 8, 4):
            out.append("<tr>")
            for w in ws[r:r + 4]:
                page_url = f"{site}w/{w['id']}.html"
                by = e(w["creator"]) + (f" · {e(w.get('made_with') or w.get('model'))}" if (w.get("made_with") or w.get("model")) else "")
                out.append(f'<td width="25%" valign="top"><a href="{page_url}"><img src="{thumb(w)}" alt="{e(title(w, lang))}"></a><br>'
                           f'<a href="{page_url}"><b>{e(title(w, lang))}</b></a><br><sub>{by}</sub></td>')
            out.append("</tr>")
        out += ["</table>", ""]
    out += ["## " + ("按标签找" if zh else "Browse by tag"), ""]
    for d in DIM_ORDER:
        top = sorted(((v, ws) for (dd, v), ws in idx.items() if dd == d), key=lambda x: -len(x[1]))[:8]
        if top:
            out.append(f"**{dlab(d, lang)}**　" + " · ".join(f"[{lab(v, lang)}]({site}{tag_path(d, v)}) <sub>{len(ws)}</sub>" for v, ws in top) + "  ")
    out += ["", "## " + ("收录标准" if zh else "Curation"), "",
            ("- 只收顶级：高审美、高方法论；不收梗图、软色情、搬运、工具广告。" if zh else "- Top-tier only: outstanding aesthetics and craft; no memes, thirst bait, reposts or tool promos."),
            ("- 视频只收 AI 视频模型生成的作品；图片只收图片模型生成的作品；大模型写代码做的（three.js、WebGL、代码渲染的视频）都归 Coding。" if zh else "- Video = AI video models only; Images = AI image models only; anything an LLM made by writing code (three.js, WebGL, code-rendered video) goes to Coding."),
            ("- 始终署名并链接原作者，从不编造提示词。" if zh else "- Creators are always credited and linked; prompts are never invented."), "",
            "## " + ("给 AI 与开发者" if zh else "For agents & developers"), "",
            f"[`works.json`]({BASE}works.json) · [`llms.txt`]({BASE}llms.txt) · [`sitemap.xml`]({BASE}sitemap.xml)", "",
            "## " + ("版权与下架" if zh else "Takedown"), "",
            (f"作品版权归原作者所有。如权利人认为收录不当，请发邮件至 **{CONTACT}** 或提 Issue，我们核实后第一时间下架。" if zh else f"All works belong to their creators. Rights holders can email **{CONTACT}** or open an issue and we will remove the work promptly."), ""]
    return "\n".join(out)


def sitemap(paths):
    urls = ""
    for p in paths:
        alts = "".join(f'<xhtml:link rel="alternate" hreflang="{T[l]["html_lang"]}" href="{BASE}{LANGS[l]}{p}"/>' for l in LANGS)
        for l in LANGS:
            urls += f"  <url><loc>{BASE}{LANGS[l]}{p}</loc><lastmod>{today}</lastmod>{alts}</url>\n"
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + urls + "</urlset>\n")


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
    for sub in ["w", "t", "en"]:
        shutil.rmtree(DOCS / sub, ignore_errors=True)
    DOCS.mkdir(exist_ok=True)
    idx = tag_index()
    paths = list(MED_PAGE.values()) + ["tags.html", "submit.html"] + [f"w/{w['id']}.html" for w in works] + [tag_path(d, v) for d, v in idx] + \
        [tag_path(d, v, m) for (d, v), ws in idx.items() for m in MED_ORDER if any(med(w) == m for w in ws)]
    files = {}
    for lang, pre in LANGS.items():
        for m in MED_ORDER:
            files[pre + MED_PAGE[m]] = build_index(lang, idx, m)
        files[pre + "tags.html"] = build_tags(idx, lang)
        files[pre + "submit.html"] = build_submit(lang)
        for w in works:
            files[f"{pre}w/{w['id']}.html"] = build_work(w, lang)
        for (d, v), ws in idx.items():
            files[pre + tag_path(d, v)] = build_tag(d, v, ws, lang)
            for m in MED_ORDER:
                if any(med(w) == m for w in ws):
                    files[pre + tag_path(d, v, m)] = build_tag_med(d, v, ws, lang, m)
    for p, s in files.items():
        f = DOCS / p; f.parent.mkdir(parents=True, exist_ok=True); f.write_text(s)
    (DOCS / "works.json").write_text(json.dumps([public_record(w) for w in works], ensure_ascii=False, indent=1))
    (DOCS / "llms.txt").write_text(llms_txt(idx))
    (DOCS / "sitemap.xml").write_text(sitemap(paths))
    (DOCS / "robots.txt").write_text(ROBOTS)
    (DOCS / ".nojekyll").write_text("")
    (ROOT / "README.md").write_text(readme(idx, "zh"))
    (ROOT / "README.en.md").write_text(readme(idx, "en"))
    print(f"{len(works)} works, {len(idx)} tags, {len(files)} html files (zh + en)")


if __name__ == "__main__":
    main()
