"""Pre-flight check: verify the Meta token, ad account, Page token, and R2 wiring
before a long run. Read-only."""
from . import metaapi


def _ok(label, detail=''):
    print(f"  [PASS] {label}" + (f" — {detail}" if detail else ''))


def _fail(label, detail=''):
    print(f"  [FAIL] {label}" + (f" — {detail}" if detail else ''))


def main(cfg, args):
    print("Ad Comment Intel — doctor\n")
    problems = 0

    # config presence
    if not cfg.path:
        print("  [FAIL] no config.env found. Run: intel setup")
        return 1
    print(f"  config: {cfg.path}\n")

    # 1) token / identity
    me = metaapi.get(cfg, 'me', {'fields': 'id,name'})
    if 'error' in me:
        _fail('Meta token', str(me['error'])[:160]); problems += 1
    else:
        _ok('Meta token', f"{me.get('name','?')} ({me.get('id','?')})")

    # 2) ad account access (spend read)
    if not cfg.acct:
        _fail('Ad account', 'META_AD_ACCOUNT_ID not set'); problems += 1
    else:
        acc = metaapi.get(cfg, cfg.acct, {'fields': 'name,account_status,currency'})
        if 'error' in acc:
            _fail('Ad account', str(acc['error'])[:160]); problems += 1
        else:
            _ok('Ad account', f"{acc.get('name','?')} [{cfg.acct}] {acc.get('currency','')}")

    # 3) page token (needed for comment reads)
    try:
        pid, pname, ptok = metaapi.page_token(cfg)
        _ok('Page token', f"{pname} ({pid})")
    except SystemExit as e:
        _fail('Page token', str(e)); problems += 1

    # 4) R2
    if not cfg.r2_ready():
        _fail('Cloudflare R2', 'incomplete keys (gallery will only build locally)'); problems += 1
    else:
        try:
            key = 'comments/_gallery/_doctor.txt'
            url = metaapi.r2_put_html(cfg, key, 'ok')
            _ok('Cloudflare R2', f"wrote {url}")
        except Exception as ex:
            _fail('Cloudflare R2', str(ex)[:160]); problems += 1

    print()
    if problems:
        print(f"{problems} problem(s). Fix the FAIL lines above, then re-run: intel doctor")
        return 1
    print("All green. You're ready: intel run")
    return 0
