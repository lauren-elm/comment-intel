"""Minimal, dependency-free Cloudflare R2 (S3-compatible) uploader using AWS
SigV4 request signing over urllib. Replaces boto3 so the kit is pure stdlib."""
import hashlib, hmac, datetime, urllib.request, urllib.parse, urllib.error


def _sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()


def put_object(r2, key, body, content_type='application/octet-stream'):
    """PUT bytes to R2 at <bucket>/<key>. `r2` is the cfg.r2() dict. Returns the
    public URL on success; raises on failure."""
    endpoint = r2['R2_ENDPOINT'].rstrip('/')           # https://<acct>.r2.cloudflarestorage.com
    host = endpoint.split('://', 1)[1]
    bucket = r2['R2_BUCKET']
    access = r2['R2_ACCESS_KEY_ID']
    secret = r2['R2_SECRET_ACCESS_KEY']
    region, service = 'auto', 's3'

    canon_key = '/'.join(urllib.parse.quote(p, safe='') for p in key.split('/'))
    canonical_uri = f'/{bucket}/{canon_key}'
    url = endpoint + canonical_uri

    now = datetime.datetime.utcnow()
    amzdate = now.strftime('%Y%m%dT%H%M%SZ')
    datestamp = now.strftime('%Y%m%d')
    payload_hash = hashlib.sha256(body).hexdigest()

    canonical_headers = (f'host:{host}\n'
                         f'x-amz-content-sha256:{payload_hash}\n'
                         f'x-amz-date:{amzdate}\n')
    signed_headers = 'host;x-amz-content-sha256;x-amz-date'
    canonical_request = (f'PUT\n{canonical_uri}\n\n'
                         f'{canonical_headers}\n{signed_headers}\n{payload_hash}')

    scope = f'{datestamp}/{region}/{service}/aws4_request'
    string_to_sign = ('AWS4-HMAC-SHA256\n'
                      f'{amzdate}\n{scope}\n'
                      + hashlib.sha256(canonical_request.encode('utf-8')).hexdigest())

    k_date = _sign(('AWS4' + secret).encode('utf-8'), datestamp)
    k_region = _sign(k_date, region)
    k_service = _sign(k_region, service)
    k_signing = _sign(k_service, 'aws4_request')
    signature = hmac.new(k_signing, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()

    authorization = (f'AWS4-HMAC-SHA256 Credential={access}/{scope}, '
                     f'SignedHeaders={signed_headers}, Signature={signature}')

    req = urllib.request.Request(url, data=body, method='PUT', headers={
        'Authorization': authorization,
        'x-amz-date': amzdate,
        'x-amz-content-sha256': payload_hash,
        'Content-Type': content_type,
        'Content-Length': str(len(body)),
    })
    with urllib.request.urlopen(req, timeout=120) as resp:
        if resp.status not in (200, 201):
            raise RuntimeError(f'R2 PUT {resp.status}')
    return f"{r2['R2_PUBLIC_BASE'].rstrip('/')}/{key}"
