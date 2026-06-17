"""Build a white-label, searchable HTML comment gallery from the JSON store and
publish it to your Cloudflare R2. Search runs on Enter; filter by media / category;
each card deep-links to the live comment on Facebook.
"""
import json, html
from . import metaapi

EMO = {'complaint': '🔴', 'question': '❓', 'positive': '🟢', 'other': '⚪'}


def flatten(comments):
    for c in comments:
        yield c
        yield from flatten(c.get('replies', []))


def fb_link(post_id, cid):
    if not post_id or '_' not in post_id:
        return ''
    page, postid = post_id.split('_', 1)
    base = f'https://www.facebook.com/{page}/posts/{postid}'
    seg = (cid or '').split('_')[-1]
    return base + (f'?comment_id={seg}' if seg else '')


def collect(cfg):
    items = []
    for f in sorted(cfg.store.glob('*.json')):
        d = json.loads(f.read_text(encoding='utf-8'))
        for c in flatten(d.get('comments', [])):
            media = c.get('media') or {}
            if media.get('skipped'):
                media = {}
            items.append({
                'text': c.get('message', '') or '',
                'cat': c.get('category', 'other'),
                'likes': c.get('likes', 0),
                'time': (c.get('created_time') or '')[:10],
                'img': media.get('r2'),
                'video': media.get('r2_video'),
                'post': d.get('post_id', ''),
                'cid': c.get('id', ''),
            })
    return items


CSS = """
:root{--bg:#0f1410;--card:#1b241c;--ink:#e8f0e6;--dim:#8aa088;--line:#2c3a2d;--accent:#1f7a33;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 -apple-system,Segoe UI,Roboto,sans-serif}
header{position:sticky;top:0;background:rgba(15,20,16,.96);backdrop-filter:blur(6px);
  border-bottom:1px solid var(--line);padding:14px 20px;z-index:5}
h1{margin:0 0 8px;font-size:18px}
.sub{color:var(--dim);font-size:13px;margin-bottom:10px}
.filters{display:flex;flex-wrap:wrap;gap:8px}
.filters button{background:var(--card);color:var(--ink);border:1px solid var(--line);
  border-radius:20px;padding:6px 14px;cursor:pointer;font-size:13px}
.filters button.on{background:var(--accent);border-color:var(--accent);color:#fff}
.search{width:100%;max-width:440px;margin-bottom:10px;background:var(--card);color:var(--ink);
  border:1px solid var(--line);border-radius:20px;padding:9px 16px;font-size:14px;outline:none}
.search:focus{border-color:var(--accent)}
.nores{display:none;color:var(--dim);text-align:center;padding:40px;font-size:14px}
.grid{column-width:300px;column-gap:16px;padding:18px}
.card{break-inside:avoid;background:var(--card);border:1px solid var(--line);border-radius:12px;
  overflow:hidden;margin:0 0 16px}
.card img,.card video{width:100%;display:block;background:#0a0d0a}
.meta{display:flex;justify-content:space-between;align-items:center;padding:8px 12px 0}
.text{padding:6px 12px 10px;white-space:pre-wrap;word-break:break-word}
.badge{font-size:11px;padding:2px 8px;border-radius:10px;border:1px solid var(--line)}
.badge.complaint{color:#ff9a9a}.badge.question{color:#9ac6ff}
.badge.positive{color:#9ff0b0}.badge.other{color:var(--dim)}
.dim{color:var(--dim);font-size:12px}
.foot{padding:0 12px 12px}
.fb{display:inline-block;font-size:12px;color:#9ac6ff;text-decoration:none;border:1px solid var(--line);
  border-radius:8px;padding:4px 10px}
.fb:hover{border-color:#9ac6ff;background:rgba(154,198,255,.08)}
"""

JS = """
const btns=document.querySelectorAll('.filters button');
const cards=document.querySelectorAll('.card');
const qbox=document.getElementById('q');
const nores=document.getElementById('nores');
let filter='all', query='';
function matchF(c){
  if(filter==='all') return true;
  if(filter==='media') return c.dataset.media!=='none';
  if(filter==='photo') return c.dataset.media==='photo';
  if(filter==='video') return c.dataset.media==='video';
  return c.dataset.cat===filter;
}
function apply(){
  let shown=0;
  cards.forEach(c=>{
    const show = matchF(c) && (!query || (c.dataset.q||'').indexOf(query)>=0);
    c.style.display = show?'':'none';
    if(show) shown++;
  });
  nores.style.display = shown?'none':'block';
}
btns.forEach(b=>b.onclick=()=>{
  btns.forEach(x=>x.classList.remove('on'));b.classList.add('on');
  filter=b.dataset.f; apply();
});
function runSearch(){ query=qbox.value.toLowerCase().trim(); apply(); }
qbox.addEventListener('search', runSearch);
qbox.addEventListener('keydown', e=>{ if(e.key==='Enter'){ e.preventDefault(); runSearch(); } });
"""


def build(cfg, upload=False):
    items = collect(cfg)
    with_media = [i for i in items if i['img'] or i.get('video')]
    n_vid = sum(1 for i in items if i.get('video'))
    n_photo = sum(1 for i in items if not i.get('video') and i['img'])
    counts = {k: sum(1 for i in items if i['cat'] == k) for k in EMO}

    cards = []
    for i in items:
        t = html.escape(i['text'])[:600]
        badge = f"{EMO.get(i['cat'], '⚪')} {i['cat']}"
        if i.get('video'):
            poster = f'poster="{html.escape(i["img"])}"' if i['img'] else ''
            mediatag = f'<video controls preload="none" {poster} src="{html.escape(i["video"])}"></video>'
        elif i['img']:
            mediatag = f'<img loading="lazy" src="{html.escape(i["img"])}" onerror="this.style.display=\'none\'">'
        else:
            mediatag = ''
        mtype = 'video' if i.get('video') else ('photo' if i['img'] else 'none')
        qtext = html.escape(i['text'].lower(), quote=True)
        link = fb_link(i['post'], i['cid'])
        linktag = (f'<a class="fb" href="{html.escape(link)}" target="_blank" rel="noopener">↗ View on Facebook</a>'
                   if link else '')
        cards.append(
            f'<div class="card" data-cat="{i["cat"]}" data-media="{mtype}" data-q="{qtext}">'
            f'{mediatag}'
            f'<div class="meta"><span class="badge {i["cat"]}">{badge}</span>'
            f'<span class="dim">♥ {i["likes"]} · {i["time"]}</span></div>'
            f'<div class="text">{t}</div>'
            f'<div class="foot">{linktag}</div></div>')

    title = html.escape(cfg.brand) + ' — Ad Comment Intel'
    sub = (f"{len(items)} comments · {len(with_media)} with media ({n_vid} video) · "
           f"🔴 {counts['complaint']} complaints · ❓ {counts['question']} questions · 🟢 {counts['positive']} positive")
    filters = (
        f'<button data-f="all" class="on">All ({len(items)})</button>'
        f'<button data-f="media">🖼 Has media ({len(with_media)})</button>'
        f'<button data-f="photo">📷 Photos ({n_photo})</button>'
        f'<button data-f="video">🎬 Videos ({n_vid})</button>'
        f'<button data-f="complaint">🔴 Complaints ({counts["complaint"]})</button>'
        f'<button data-f="question">❓ Questions ({counts["question"]})</button>'
        f'<button data-f="positive">🟢 Positive ({counts["positive"]})</button>')

    doc = (
        '<!doctype html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{title}</title><style>{CSS}</style></head><body>'
        f'<header><h1>{title}</h1><div class="sub">{sub}</div>'
        '<input id="q" class="search" type="search" placeholder="🔎 Search comment text — press Enter" autocomplete="off">'
        f'<div class="filters">{filters}</div></header>'
        f'<div class="grid" id="grid">{"".join(cards)}</div>'
        '<div class="nores" id="nores">No comments match your search + filter.</div>'
        f'<script>{JS}</script></body></html>')

    out = cfg.outdir / 'comment-gallery.html'
    out.write_text(doc, encoding='utf-8')
    print(f"comments: {len(items)} | with media: {len(with_media)} ({n_vid} video)")
    print(f"Local gallery: {out}")
    url = None
    if upload:
        if not cfg.r2_ready():
            print("  ! R2 not configured — skipping upload. Run `intel setup` to add R2 keys.")
        else:
            key = f"comments/_gallery/{cfg.brand_slug}-comment-gallery.html"
            url = metaapi.r2_put_html(cfg, key, doc)
            print(f"CLOUD URL: {url}")
    return out, url


def main(cfg, args):
    return build(cfg, upload=not args.no_upload)
