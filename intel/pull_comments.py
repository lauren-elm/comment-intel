"""Scrape comments + reply threads off a set of ad posts. READ-ONLY on Facebook.

Captures text + engagement + photo/video attachments (mirrored to your R2),
light-classifies each comment, and writes a per-post JSON store. Resumable via
skip_existing. Writes NOTHING to Facebook — no replies, hides, or bans.
"""
import sys, re, json, time
from . import metaapi

COMPLAINT = re.compile(r'\b(scam|refund|never (came|arrived|got|received)|waste|charged?|cancel|'
                       r'warning|fake|disappointed|still waiting|no confirmation|did(n.?t| not) work|'
                       r'does(n.?t| not) work|rip ?off|fraud|stop)\b', re.I)
POSITIVE = re.compile(r'\b(love|great|amazing|thank|beautiful|gorgeous|works great|best|awesome|'
                      r'wonderful|excellent|incredible|obsessed|game ?changer)\b', re.I)
QWORD = re.compile(r'^(how|what|where|when|can|does|do|is|are|will|would|has|have|any)\b', re.I)
SCAM = re.compile(r'\b(scam|fraud|fake|rip ?off|bull ?shit|\bbs\b|garbage|trash|junk|crap)\b', re.I)
GIF_TYPES = {'animated_image_share', 'animated_image_video', 'animated_image_autoplay'}

CFIELDS = ('id,message,created_time,like_count,comment_count,is_hidden,'
           'attachment{type,media{image{src},source},target{id,url},url,'
           'subattachments{type,media{image{src},source}}}')


def classify(msg):
    m = (msg or '').strip()
    if COMPLAINT.search(m):
        return 'complaint'
    if '?' in m or QWORD.match(m):
        return 'question'
    if POSITIVE.search(m):
        return 'positive'
    return 'other'


def media_from_attachment(att):
    t = (att.get('type') or '').lower()
    media = att.get('media') or {}
    img = (media.get('image') or {}).get('src')
    vid = media.get('source')
    if not vid:
        for sub in (att.get('subattachments') or {}).get('data', []):
            sm = sub.get('media') or {}
            if sm.get('source'):
                vid = sm.get('source'); img = img or (sm.get('image') or {}).get('src'); break
    if t in GIF_TYPES:
        kind = 'gif'
    elif 'video' in t or vid:
        kind = 'video'
    elif img:
        kind = 'photo'
    else:
        kind = t or 'other'
    if not (img or vid):
        return None
    return {'kind': kind, 'type': att.get('type'), 'img': img, 'video': vid, 'url': att.get('url')}


def keep_media(rec):
    m = rec.get('media')
    if not m:
        return False
    if m['kind'] == 'gif':
        return False
    if SCAM.search(rec.get('message', '') or ''):
        return False
    return True


def pull_comments(cfg, obj_id, tok, cap):
    rows = metaapi.paged(cfg, obj_id + '/comments',
                         {'order': 'chronological', 'limit': '100', 'filter': 'stream', 'fields': CFIELDS},
                         tok, cap=cap)
    out = []
    for c in rows:
        rec = {'id': c['id'], 'message': c.get('message', ''), 'created_time': c.get('created_time'),
               'likes': c.get('like_count', 0), 'reply_count': c.get('comment_count', 0),
               'is_hidden': c.get('is_hidden', False),
               'category': classify(c.get('message', '')), 'media': None, 'replies': []}
        att = c.get('attachment')
        if att:
            rec['media'] = media_from_attachment(att)
        out.append((rec, c.get('comment_count', 0)))
    return out


def count_comments(cfg, sid, tok):
    s = metaapi.get(cfg, sid + '/comments', {'summary': 'true', 'limit': '0'}, tok)
    return s.get('summary', {}).get('total_count', 0) if 'error' not in s else 0


def run_batch(cfg, post_ids, skip_existing=True, no_replies=False, no_r2=False):
    pid, pname, ptok = metaapi.page_token(cfg)
    print(f"PAGE: {pname} ({pid})")
    store = cfg.store
    max_per = int(cfg.num('MAX_PER_POST', 2000))
    min_comments = int(cfg.num('MIN_COMMENTS', 1))

    ids = sorted(set(post_ids))
    ranked = []
    for sid in ids:
        n = count_comments(cfg, sid, ptok)
        if n >= min_comments:
            ranked.append((sid, n))
    ranked.sort(key=lambda x: -x[1])
    empty = len(ids) - len(ranked)
    print(f"{len(ids)} posts -> {len(ranked)} with >= {min_comments} comments ({empty} returned 0)")

    totals = {'posts': 0, 'comments': 0, 'replies': 0, 'photos': 0, 'videos': 0, 'skipped_junk': 0,
              'complaint': 0, 'question': 0, 'positive': 0, 'other': 0, 'empty_posts': empty}
    stamp = time.strftime('%Y-%m-%d')

    for idx, (sid, n) in enumerate(ranked, 1):
        jpath = store / f"{sid.replace('_', '-')}.json"
        if skip_existing and jpath.exists():
            print(f"  ({idx}/{len(ranked)}) skip existing {sid}")
            continue
        print(f"  ({idx}/{len(ranked)}) [{n:>4} comments] {sid}")
        comments = pull_comments(cfg, sid, ptok, max_per)

        def mirror(rec):
            m = rec.get('media')
            if not m:
                return
            if not keep_media(rec):
                m['skipped'] = True; totals['skipped_junk'] += 1; return
            cid = rec['id'].split('_')[-1]
            if m.get('video'):
                if not no_r2:
                    vurl = metaapi.r2_put_url(cfg, m['video'], f"comments/{sid}/{cid}.mp4")
                    if vurl:
                        m['r2_video'] = vurl
                    if m.get('img'):
                        turl = metaapi.r2_put_url(cfg, m['img'], f"comments/{sid}/{cid}.jpg")
                        if turl:
                            m['r2'] = turl
                totals['videos'] += 1
            elif m.get('img'):
                if not no_r2:
                    url = metaapi.r2_put_url(cfg, m['img'], f"comments/{sid}/{cid}.jpg")
                    if url:
                        m['r2'] = url
                totals['photos'] += 1

        recs = []
        for rec, rcount in comments:
            if rcount and not no_replies:
                for r, _ in pull_comments(cfg, rec['id'], ptok, max_per):
                    mirror(r); rec['replies'].append(r); totals['replies'] += 1
            mirror(rec)
            totals[rec['category']] += 1
            recs.append(rec)

        jpath.write_text(json.dumps(
            {'post_id': sid, 'pulled': stamp, 'comment_count_reported': n, 'comments': recs},
            indent=2, ensure_ascii=False), encoding='utf-8')
        totals['posts'] += 1
        totals['comments'] += len(recs)

    print("\n=== TOTALS ===")
    for k, v in totals.items():
        print(f"  {k}: {v}")
    print(f"JSON store: {store}")
    return totals


def main(cfg, args):
    listfile = cfg.outdir / 'post_list.txt'
    if not listfile.exists():
        raise SystemExit(f"No {listfile}. Run `rank` or `run` first (it writes the pull list).")
    ids = [l.strip() for l in listfile.read_text(encoding='utf-8').splitlines()
           if l.strip() and not l.startswith('#')]
    return run_batch(cfg, ids, skip_existing=not args.fresh,
                     no_replies=args.no_replies, no_r2=args.no_r2)
