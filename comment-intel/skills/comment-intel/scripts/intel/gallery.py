"""Build a white-label, searchable comment gallery from the JSON store and publish
it to your Cloudflare R2. Mobile-friendly: comment data is embedded as JSON and
cards render incrementally on scroll, so even 20k+ comments stay fast on a phone.
Search runs on Enter; filter by media / category; each card deep-links to the live
comment on Facebook. Also writes a flat CSV export.
"""
import csv, json, html
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
header{position:sticky;top:0;background:rgba(15,20,16,.97);backdrop-filter:blur(6px);
  border-bottom:1px solid var(--line);padding:12px 16px;z-index:5}
h1{margin:0 0 6px;font-size:17px}
.sub{color:var(--dim);font-size:12px;margin-bottom:9px}
.filters{display:flex;flex-wrap:wrap;gap:7px}
.filters button{background:var(--card);color:var(--ink);border:1px solid var(--line);
  border-radius:20px;padding:6px 13px;cursor:pointer;font-size:13px}
.filters button.on{background:var(--accent);border-color:var(--accent);color:#fff}
.search{width:100%;margin-bottom:9px;background:var(--card);color:var(--ink);
  border:1px solid var(--line);border-radius:20px;padding:10px 16px;font-size:16px;outline:none}
.search:focus{border-color:var(--accent)}
#count{display:block;margin-top:8px;color:var(--dim);font-size:12px}
.nores{display:none;color:var(--dim);text-align:center;padding:40px;font-size:14px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:14px;padding:16px}
@media(max-width:560px){.grid{grid-template-columns:1fr;gap:12px;padding:12px}}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden}
.card img,.card video{width:100%;display:block;background:#0a0d0a}
.meta{display:flex;justify-content:space-between;align-items:center;padding:8px 12px 0;gap:8px}
.text{padding:6px 12px 10px;white-space:pre-wrap;word-break:break-word}
.badge{font-size:11px;padding:2px 8px;border-radius:10px;border:1px solid var(--line);white-space:nowrap}
.badge.complaint{color:#ff9a9a}.badge.question{color:#9ac6ff}
.badge.positive{color:#9ff0b0}.badge.other{color:var(--dim)}
.dim{color:var(--dim);font-size:12px}
.foot{padding:0 12px 12px}
.fb{display:inline-block;font-size:12px;color:#9ac6ff;text-decoration:none;border:1px solid var(--line);
  border-radius:8px;padding:5px 11px}
.fb:hover{border-color:#9ac6ff;background:rgba(154,198,255,.08)}
"""

JS = """
const EMO={complaint:'🔴',question:'❓',positive:'🟢',other:'⚪'};
const DATA=__DATA__;
const grid=document.getElementById('grid');
const sentinel=document.getElementById('more');
const nores=document.getElementById('nores');
const counter=document.getElementById('count');
const qbox=document.getElementById('q');
const btns=document.querySelectorAll('.filters button');
let filter='all', query='', shown=0, filtered=DATA;
const BATCH=40;
function matchF(o){
  if(filter==='all')return true;
  if(filter==='media')return !!o.m;
  if(filter==='photo')return o.m&&!o.v;
  if(filter==='video')return !!o.v;
  return o.c===filter;
}
function esc(s){const d=document.createElement('div');d.textContent=s||'';return d.innerHTML;}
function card(o){
  let media='';
  if(o.v){media='<video controls preload="none" '+(o.p?('poster="'+o.p+'" '):'')+'src="'+o.m+'"></video>';}
  else if(o.m){media='<img loading="lazy" src="'+o.m+'" onerror="this.style.display=\\'none\\'">';}
  const link=o.f?('<a class="fb" href="'+o.f+'" target="_blank" rel="noopener">↗ View on Facebook</a>'):'';
  return '<div class="card">'+media+'<div class="meta"><span class="badge '+o.c+'">'+(EMO[o.c]||'⚪')+' '+o.c+
    '</span><span class="dim">♥ '+(o.l||0)+' · '+(o.d||'')+'</span></div><div class="text">'+
    esc(o.t)+'</div><div class="foot">'+link+'</div></div>';
}
function renderMore(){
  const next=filtered.slice(shown,shown+BATCH);
  if(next.length){grid.insertAdjacentHTML('beforeend',next.map(card).join(''));shown+=next.length;}
  sentinel.style.display=(shown<filtered.length)?'block':'none';
}
function apply(){
  filtered=DATA.filter(matchF);
  if(query){filtered=filtered.filter(function(o){return (o.t||'').toLowerCase().indexOf(query)>=0;});}
  grid.innerHTML='';shown=0;
  counter.textContent=filtered.length.toLocaleString()+' shown';
  nores.style.display=filtered.length?'none':'block';
  renderMore();
}
btns.forEach(function(b){b.onclick=function(){btns.forEach(function(x){x.classList.remove('on');});b.classList.add('on');filter=b.dataset.f;apply();};});
function runSearch(){query=qbox.value.toLowerCase().trim();apply();}
qbox.addEventListener('search',runSearch);
qbox.addEventListener('keydown',function(e){if(e.key==='Enter'){e.preventDefault();runSearch();}});
new IntersectionObserver(function(es){if(es[0].isIntersecting)renderMore();},{rootMargin:'600px'}).observe(sentinel);
apply();
"""


def build(cfg, upload=False):
    items = collect(cfg)
    with_media = [i for i in items if i['img'] or i.get('video')]
    n_vid = sum(1 for i in items if i.get('video'))
    n_photo = sum(1 for i in items if not i.get('video') and i['img'])
    counts = {k: sum(1 for i in items if i['cat'] == k) for k in EMO}

    # compact data array for client-side incremental rendering (mobile-friendly)
    data = []
    for i in items:
        o = {'t': (i['text'] or '')[:400], 'c': i['cat'], 'l': i['likes'], 'd': i['time']}
        f = fb_link(i['post'], i['cid'])
        if f:
            o['f'] = f
        if i.get('video'):
            o['v'] = 1; o['m'] = i['video']
            if i['img']:
                o['p'] = i['img']
        elif i['img']:
            o['m'] = i['img']
        data.append(o)
    datajson = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')
    js = JS.replace('__DATA__', datajson)

    title = html.escape(cfg.brand) + ' — Ad Comment Intel'
    sub = (f"{len(items):,} comments · {len(with_media):,} with media ({n_vid} video) · "
           f"🔴 {counts['complaint']:,} · ❓ {counts['question']:,} · 🟢 {counts['positive']:,}")
    filters = (
        f'<button data-f="all" class="on">All ({len(items):,})</button>'
        f'<button data-f="media">🖼 Media ({len(with_media):,})</button>'
        f'<button data-f="photo">📷 Photos ({n_photo:,})</button>'
        f'<button data-f="video">🎬 Videos ({n_vid})</button>'
        f'<button data-f="complaint">🔴 Complaints ({counts["complaint"]:,})</button>'
        f'<button data-f="question">❓ Questions ({counts["question"]:,})</button>'
        f'<button data-f="positive">🟢 Positive ({counts["positive"]:,})</button>')

    doc = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{title}</title><style>{CSS}</style></head><body>'
        f'<header><h1>{title}</h1><div class="sub">{sub}</div>'
        '<input id="q" class="search" type="search" placeholder="🔎 Search comment text — press Enter" autocomplete="off">'
        f'<div class="filters">{filters}</div><span id="count"></span></header>'
        '<div class="grid" id="grid"></div>'
        '<div id="more" style="height:1px"></div>'
        '<div class="nores" id="nores">No comments match your search + filter.</div>'
        f'<script>{js}</script></body></html>')

    out = cfg.outdir / 'comment-gallery.html'
    out.write_text(doc, encoding='utf-8')
    csv_text = export_csv(cfg, items)
    print(f"comments: {len(items)} | with media: {len(with_media)} ({n_vid} video)")
    print(f"Local gallery: {out}")
    print(f"Local data export: {cfg.outdir / 'comments_export.csv'}")
    url = None
    if upload:
        if not cfg.r2_ready():
            print("  ! R2 not configured — skipping upload. Run `intel setup` to add R2 keys.")
        else:
            url = metaapi.r2_put_html(cfg, f"comments/_gallery/{cfg.brand_slug}-comment-gallery.html", doc)
            csv_url = metaapi.r2_put_text(cfg, f"comments/_gallery/{cfg.brand_slug}-comments.csv",
                                          csv_text, 'text/csv; charset=utf-8')
            print(f"CLOUD URL: {url}")
            print(f"DATA CSV:  {csv_url}")
    return out, url


def export_csv(cfg, items):
    """Write a flat machine-readable CSV of every comment (one row each).
    Returns the CSV text (also written to output/comments_export.csv)."""
    import io
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(['post_id', 'comment_id', 'category', 'likes', 'date',
                'media_url', 'facebook_link', 'text'])
    for i in items:
        media = i.get('video') or i.get('img') or ''
        text = (i['text'] or '').replace('\r', ' ').replace('\n', '  ')
        w.writerow([i['post'], i['cid'], i['cat'], i['likes'], i['time'],
                    media, fb_link(i['post'], i['cid']), text])
    csv_text = buf.getvalue()
    (cfg.outdir / 'comments_export.csv').write_text('﻿' + csv_text, encoding='utf-8')
    return csv_text


def main(cfg, args):
    return build(cfg, upload=not args.no_upload)
