"""Graph API + Cloudflare R2 helpers. Read-only against Facebook."""
import sys, json, time, urllib.request, urllib.parse, urllib.error

UA = 'Mozilla/5.0 (ad-comment-intel)'


def _base(cfg):
    return f'https://graph.facebook.com/{cfg.gver}/'


def _is_transient(code, body):
    return (code in (429, 500, 503, 613)
            or '"code":4' in body or '"code":17' in body
            or 'is_transient":true' in body)


def get_url(cfg, url):
    """GET a fully-formed Graph URL (used for cursor `paging.next`), with backoff."""
    for attempt in range(6):
        try:
            with urllib.request.urlopen(url, timeout=90) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            if _is_transient(e.code, body) and attempt < 5:
                wait = 60 if ('"code":4' in body or '"code":17' in body or e.code == 613) else 2 ** attempt
                print(f"    ...transient ({e.code}); waiting {wait}s", file=sys.stderr)
                time.sleep(wait); continue
            try:
                return {'error': json.loads(body).get('error', body)}
            except Exception:
                return {'error': body}
        except urllib.error.URLError:
            if attempt < 5:
                time.sleep(2 ** attempt); continue
            return {'error': 'network error'}
    return {'error': 'retries exhausted'}


def get(cfg, path, params, tok=None):
    params = dict(params); params['access_token'] = tok or cfg.token
    return get_url(cfg, _base(cfg) + path + '?' + urllib.parse.urlencode(params))


def paged(cfg, path, params, tok=None, cap=10**9):
    out = []
    resp = get(cfg, path, params, tok)
    while True:
        if 'error' in resp:
            if not out:
                print(f"    ! {path}: {resp['error']}", file=sys.stderr)
            break
        out.extend(resp.get('data', []))
        if len(out) >= cap:
            return out[:cap]
        nxt = resp.get('paging', {}).get('next')
        if not nxt:
            break
        resp = get_url(cfg, nxt)
    return out


def batch(cfg, calls, tok=None):
    """POST a Graph batch (max 50 calls). Returns the array of sub-responses."""
    data = urllib.parse.urlencode({'access_token': tok or cfg.token,
                                   'batch': json.dumps(calls)}).encode()
    for attempt in range(6):
        try:
            req = urllib.request.Request(_base(cfg), data=data)
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            if _is_transient(e.code, body) and attempt < 5:
                time.sleep(60 if ('"code":4' in body) else 2 ** attempt); continue
            print(f"    ! batch {e.code}: {body[:300]}", file=sys.stderr)
            return []
        except urllib.error.URLError:
            if attempt < 5:
                time.sleep(2 ** attempt); continue
            return []
    return []


def page_token(cfg, tok=None):
    """Resolve (page_id, page_name, page_access_token). Uses META_PAGE_ID if set."""
    tok = tok or cfg.token
    a = get(cfg, 'me/accounts', {'fields': 'id,name,access_token', 'limit': '200'}, tok)
    data = a.get('data') or []
    if data:
        if cfg.page_id:
            for pg in data:
                if pg['id'] == cfg.page_id:
                    return pg['id'], pg.get('name', ''), pg['access_token']
            print(f"    ! META_PAGE_ID {cfg.page_id} not in your pages; using first.", file=sys.stderr)
        pg = data[0]
        return pg['id'], pg.get('name', ''), pg['access_token']
    if cfg.page_id:                      # token may already be page-scoped
        nm = get(cfg, cfg.page_id, {'fields': 'name'}, tok).get('name', '')
        return cfg.page_id, nm, tok
    raise SystemExit('No Facebook Page found on this token. Set META_PAGE_ID and ensure '
                     'the token has pages_show_list / pages_read_user_content.')


# ---------- Cloudflare R2 ----------
_R2 = {'client': None}


def r2_client(cfg):
    if _R2['client'] is None:
        import boto3
        r = cfg.r2()
        _R2['client'] = boto3.client(
            's3', endpoint_url=r['R2_ENDPOINT'],
            aws_access_key_id=r['R2_ACCESS_KEY_ID'],
            aws_secret_access_key=r['R2_SECRET_ACCESS_KEY'], region_name='auto')
    return _R2['client']


def r2_put_url(cfg, src_url, key):
    """Download a media URL and mirror it to R2; return the public URL (or None)."""
    r = cfg.r2()
    if not src_url or not r.get('R2_BUCKET'):
        return None
    try:
        req = urllib.request.Request(src_url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = resp.read(); ctype = resp.headers.get('Content-Type', 'image/jpeg')
        r2_client(cfg).put_object(Bucket=r['R2_BUCKET'], Key=key, Body=body, ContentType=ctype)
        return f"{r['R2_PUBLIC_BASE'].rstrip('/')}/{key}"
    except Exception as ex:
        print(f"    ! R2 mirror failed ({key}): {ex}", file=sys.stderr)
        return None


def r2_put_html(cfg, key, htmldoc):
    r = cfg.r2()
    r2_client(cfg).put_object(Bucket=r['R2_BUCKET'], Key=key,
                              Body=htmldoc.encode('utf-8'),
                              ContentType='text/html; charset=utf-8')
    return f"{r['R2_PUBLIC_BASE'].rstrip('/')}/{key}"
