"""Config loader. Reads a single `config.env` (key=value) plus environment overrides."""
import os, re, pathlib

KEYS = (
    'META_ACCESS_TOKEN', 'META_AD_ACCOUNT_ID', 'META_PAGE_ID', 'GRAPH_VERSION',
    'BRAND_NAME', 'MONTHS_BACK', 'MIN_SPEND', 'MIN_ROAS', 'TOP_BY_SPEND',
    'MIN_COMMENTS', 'MAX_PER_POST', 'OUTPUT_DIR',
    'R2_ACCOUNT_ID', 'R2_ACCESS_KEY_ID', 'R2_SECRET_ACCESS_KEY',
    'R2_BUCKET', 'R2_ENDPOINT', 'R2_PUBLIC_BASE',
)


def find_config():
    p = os.environ.get('INTEL_CONFIG')
    if p and pathlib.Path(p).expanduser().exists():
        return pathlib.Path(p).expanduser()
    for cand in (pathlib.Path.cwd() / 'config.env',
                 pathlib.Path(__file__).resolve().parent.parent / 'config.env'):
        if cand.exists():
            return cand
    return None


class Config(dict):
    path = None

    @property
    def token(self):
        return self.get('META_ACCESS_TOKEN', '').strip()

    @property
    def acct(self):
        a = self.get('META_AD_ACCOUNT_ID', '').strip()
        if not a:
            return ''
        return a if a.startswith('act_') else 'act_' + a

    @property
    def gver(self):
        return self.get('GRAPH_VERSION', '').strip() or 'v21.0'

    @property
    def page_id(self):
        return self.get('META_PAGE_ID', '').strip()

    @property
    def brand(self):
        return self.get('BRAND_NAME', '').strip() or 'Your Brand'

    @property
    def brand_slug(self):
        return re.sub(r'[^a-z0-9]+', '-', self.brand.lower()).strip('-') or 'brand'

    def num(self, key, default):
        try:
            return float(self.get(key, '') or default)
        except ValueError:
            return float(default)

    @property
    def outdir(self):
        d = pathlib.Path(self.get('OUTPUT_DIR', '').strip() or (pathlib.Path.cwd() / 'output'))
        d.mkdir(parents=True, exist_ok=True)
        return d

    def sub(self, name):
        d = self.outdir / name
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def store(self):
        return self.sub('comment_store')

    @property
    def cache(self):
        return self.sub('cache')

    def r2(self):
        return {k: self.get(k, '').strip() for k in (
            'R2_ACCOUNT_ID', 'R2_ACCESS_KEY_ID', 'R2_SECRET_ACCESS_KEY',
            'R2_BUCKET', 'R2_ENDPOINT', 'R2_PUBLIC_BASE')}

    def r2_ready(self):
        r = self.r2()
        return all(r[k] for k in ('R2_ACCESS_KEY_ID', 'R2_SECRET_ACCESS_KEY',
                                  'R2_BUCKET', 'R2_ENDPOINT', 'R2_PUBLIC_BASE'))


def load():
    cfg = Config()
    path = find_config()
    if path:
        cfg.path = path
        for line in path.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                cfg[k.strip()] = v.strip().strip('"').strip("'")
    for k in KEYS:                       # env vars win over file
        if os.environ.get(k):
            cfg[k] = os.environ[k]
    return cfg
