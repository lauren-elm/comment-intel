"""Rank ad POSTS by spend and FB-attributed ROI over a rolling window.

Spend + revenue are aggregated per underlying post (effective_object_story_id),
because one post usually backs many ads. ROI basis = Meta `omni_purchase` value
(FB-attributed revenue / spend) — a directional indicator, richer than last-touch
funnel truth. Monthly pulls are cached so re-runs are fast and rate-limit-safe.
"""
import os, csv, json, datetime, urllib.parse
from . import metaapi


def month_windows(months_back):
    today = datetime.date.today()
    y, m = today.year, today.month
    out = []
    for i in range(int(months_back) - 1, -1, -1):
        yy, mm = y, m - i
        while mm <= 0:
            mm += 12; yy -= 1
        first = datetime.date(yy, mm, 1)
        nxt = datetime.date(yy + 1, 1, 1) if mm == 12 else datetime.date(yy, mm + 1, 1)
        last = min(nxt - datetime.timedelta(days=1), today)
        out.append((first.isoformat(), last.isoformat()))
    return out


def _omni(row, field):
    for a in row.get(field, []) or []:
        if a.get('action_type') == 'omni_purchase':
            return float(a.get('value', 0) or 0)
    return 0.0


def _pull_month(cfg, since, until):
    rows = []
    params = {'level': 'ad', 'time_range': json.dumps({'since': since, 'until': until}),
              'fields': 'ad_id,spend,action_values', 'limit': '500', 'access_token': cfg.token}
    url = f'https://graph.facebook.com/{cfg.gver}/{cfg.acct}/insights?' + urllib.parse.urlencode(params)
    while url:
        d = metaapi.get_url(cfg, url)
        if 'error' in d:
            print(f"    ! {since[:7]} insights: {d['error']}")
            break
        rows.extend(d.get('data', []))
        url = d.get('paging', {}).get('next')
    return rows


def link(sid):
    if '_' in sid:
        page, post = sid.split('_', 1)
        return f'https://www.facebook.com/{page}/posts/{post}'
    return f'https://www.facebook.com/{sid}'


def rank(cfg):
    """Return {post_id: {spend, rev, ads}} aggregated over the window."""
    wins = month_windows(cfg.num('MONTHS_BACK', 13))
    current_label = wins[-1][0][:7]
    ad = {}
    print(f"Window: {wins[0][0]} -> {wins[-1][1]}  ({len(wins)} months)")
    for since, until in wins:
        label = since[:7]
        cf = cfg.cache / f'{label}.json'
        # always re-pull the current (incomplete) month for fresh spend
        if cf.exists() and label != current_label:
            rows = json.loads(cf.read_text(encoding='utf-8'))
            tag = 'cached'
        else:
            rows = _pull_month(cfg, since, until)
            cf.write_text(json.dumps(rows), encoding='utf-8')
            tag = 'pulled'
        for r in rows:
            sp = float(r.get('spend', 0) or 0)
            if sp <= 0:
                continue
            a = ad.setdefault(r['ad_id'], {'spend': 0.0, 'rev': 0.0})
            a['spend'] += sp
            a['rev'] += _omni(r, 'action_values')
        print(f"  {label} {tag:7} (ads so far: {len(ad)})")

    # map ad_id -> post (cached)
    smap_path = cfg.cache / '_story_map.json'
    smap = json.loads(smap_path.read_text(encoding='utf-8')) if smap_path.exists() else {}
    todo = [a for a in ad if a not in smap]
    if todo:
        print(f"Mapping {len(todo)} new ads to posts ({len(smap)} cached)...")
    for i in range(0, len(todo), 50):
        chunk = todo[i:i + 50]
        calls = [{'method': 'GET',
                  'relative_url': f'{a}?fields=creative{{effective_object_story_id,object_story_id}}'}
                 for a in chunk]
        arr = metaapi.batch(cfg, calls)
        for a, item in zip(chunk, arr):
            sid = None
            if item and item.get('code') == 200:
                cr = json.loads(item['body']).get('creative', {}) or {}
                sid = cr.get('effective_object_story_id') or cr.get('object_story_id')
            smap[a] = sid
        smap_path.write_text(json.dumps(smap), encoding='utf-8')

    posts = {}
    for a, v in ad.items():
        sid = smap.get(a)
        if not sid:
            continue
        p = posts.setdefault(sid, {'spend': 0.0, 'rev': 0.0, 'ads': 0})
        p['spend'] += v['spend']; p['rev'] += v['rev']; p['ads'] += 1
    return posts, wins


def cuts(cfg, posts):
    """Return (by_spend, roi_cut) lists of (sid, spend, rev, roas, ads)."""
    rows = []
    for sid, v in posts.items():
        roas = v['rev'] / v['spend'] if v['spend'] else 0.0
        rows.append((sid, v['spend'], v['rev'], roas, v['ads']))
    by_spend = sorted(rows, key=lambda r: -r[1])
    min_spend = cfg.num('MIN_SPEND', 300)
    min_roas = cfg.num('MIN_ROAS', 1.0)
    roi = [r for r in by_spend if r[1] >= min_spend and r[3] > min_roas]
    return by_spend, roi


def write_csvs(cfg, by_spend, roi):
    out = cfg.outdir
    with open(out / 'posts_by_spend.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(['rank', 'post_id', 'spend', 'fb_revenue', 'roas', 'ads', 'link'])
        for i, (sid, sp, rev, roas, ads) in enumerate(by_spend, 1):
            w.writerow([i, sid, f'{sp:.2f}', f'{rev:.2f}', f'{roas:.2f}', ads, link(sid)])
    with open(out / 'posts_positive_roi.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(['rank', 'post_id', 'spend', 'fb_revenue', 'roas', 'ads', 'link'])
        for i, (sid, sp, rev, roas, ads) in enumerate(roi, 1):
            w.writerow([i, sid, f'{sp:.2f}', f'{rev:.2f}', f'{roas:.2f}', ads, link(sid)])


def select(cfg, posts):
    """The pull list = positive-ROI posts UNION top-N highest spenders."""
    by_spend, roi = cuts(cfg, posts)
    ids = set(r[0] for r in roi)
    topn = int(cfg.num('TOP_BY_SPEND', 20))
    if topn:
        ids |= set(r[0] for r in by_spend[:topn])
    return ids, by_spend, roi


def main(cfg, args):
    posts, wins = rank(cfg)
    ids, by_spend, roi = select(cfg, posts)
    write_csvs(cfg, by_spend, roi)
    (cfg.outdir / 'post_list.txt').write_text(
        '# selected ad posts (top spenders + positive ROI)\n' + '\n'.join(sorted(ids)) + '\n',
        encoding='utf-8')
    tot_sp = sum(r[1] for r in by_spend)
    print(f"\nRanked {len(posts)} posts | total spend ${tot_sp:,.0f}")
    print(f"Positive-ROI (spend>=${cfg.num('MIN_SPEND',300):.0f} & ROAS>{cfg.num('MIN_ROAS',1):.2f}): {len(roi)}")
    print(f"Selected for comment pull (ROI + top {int(cfg.num('TOP_BY_SPEND',20))} spend): {len(ids)}")
    print(f"\nCSVs: {cfg.outdir/'posts_by_spend.csv'} , posts_positive_roi.csv")
    print(f"Pull list: {cfg.outdir/'post_list.txt'}")
    return ids
