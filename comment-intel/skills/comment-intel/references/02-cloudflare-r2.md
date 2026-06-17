# 2 · Set up Cloudflare R2 (free hosting)

R2 is Cloudflare's object storage. It hosts your **gallery HTML** and the **mirrored photos/videos**, and serves them over a public URL. The free tier (10 GB storage + generous egress) is plenty for this.

Time: ~10 minutes, once.

---

## A. Create the bucket

1. Sign in / sign up at **https://dash.cloudflare.com** (free).
2. Left sidebar → **R2**. If prompted, enable R2 (you may need to add a card, but the free tier won't charge).
3. **Create bucket** → name it e.g. `ad-comment-intel` → Create.

Copy your **Account ID** — it's on the R2 overview page (and in the dashboard URL). This is `R2_ACCOUNT_ID`.

---

## B. Create an API token (S3 keys)

1. In **R2 → Manage R2 API Tokens** (a.k.a. "API Tokens" on the R2 page) → **Create API token**.
2. Permissions: **Object Read & Write**.
3. (Optional) scope it to just your bucket.
4. Create. You'll get an **Access Key ID** and a **Secret Access Key** — copy both now (the secret is shown once).
   - `R2_ACCESS_KEY_ID`
   - `R2_SECRET_ACCESS_KEY`

Your S3 endpoint is:
```
https://<R2_ACCOUNT_ID>.r2.cloudflarestorage.com
```
That's `R2_ENDPOINT` (the setup wizard fills it in automatically from your account id).

---

## C. Make the bucket public (so the gallery has a URL)

Pick **one** of these:

### Option 1 — Custom domain (recommended, clean URLs)
1. Bucket → **Settings → Public access → Custom Domains → Connect Domain**.
2. Enter a subdomain you control on Cloudflare, e.g. `files.yourdomain.com`.
3. Cloudflare adds the DNS record automatically (if the domain's on your Cloudflare account). Wait for "Active".
4. `R2_PUBLIC_BASE = https://files.yourdomain.com`

### Option 2 — r2.dev dev URL (fastest, no domain needed)
1. Bucket → **Settings → Public access → R2.dev subdomain → Allow Access**.
2. You'll get a URL like `https://pub-abc123.r2.dev`.
3. `R2_PUBLIC_BASE = https://pub-abc123.r2.dev`

> The r2.dev URL is rate-limited and meant for dev/sharing, which is fine here. Use a custom domain if you'll share widely.

---

## D. Plug it in

If you haven't run setup yet, do `python comment_intel.py setup` and paste these when asked. Or edit `config.env`:

```
R2_ACCOUNT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
R2_ACCESS_KEY_ID=xxxxxxxxxxxxxxxxxxxx
R2_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
R2_BUCKET=ad-comment-intel
R2_ENDPOINT=https://<account_id>.r2.cloudflarestorage.com
R2_PUBLIC_BASE=https://files.yourdomain.com
```

Verify:
```bash
python comment_intel.py doctor
```
should show **[PASS] Cloudflare R2 — wrote https://…/_doctor.txt**.

➡️ Next: **[Usage & the flow](03-usage.md)**
