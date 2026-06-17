# 4 · Troubleshooting

Run `python -m intel doctor` first — it pinpoints which connection is broken.

---

### "No config found (or token missing)"
You haven't run onboarding, or you're in the wrong folder. `config.env` must be in the folder you run commands from. Fix: `python -m intel setup`.

### Meta token FAIL / "Error validating access token"
- The token expired (Graph Explorer tokens last ~1–2 hours). Use a **System User token** (docs/01, section C) for anything ongoing.
- The token is missing scopes. Regenerate it with `ads_read`, `read_insights`, `pages_show_list`, `pages_read_user_content`.

### Ad account FAIL / "(#100) … nonexisting field" / empty spend
- Wrong `META_AD_ACCOUNT_ID`. Use the digits only (no `act_`).
- The System User isn't assigned to that ad account. Business Settings → System Users → your user → Add Assets → the ad account → View Performance.

### Page token FAIL / "No Facebook Page found"
- The token lacks `pages_show_list`, or the System User isn't assigned to the Page. Assign the Page to the System User and regenerate the token.
- If you manage many Pages and it picked the wrong one, set `META_PAGE_ID` in `config.env` to the right id.

### "Application request limit reached" / code 4 / it slows down
That's Meta's rate limit. The kit **automatically backs off and retries** (up to ~60s waits). For very large accounts:
- Let it keep running — it resumes and is patient.
- If it stops, just run the command again — scraping is resumable (`--skip` is automatic; already-pulled posts are skipped).
- `--no-replies` roughly halves the API calls.

### A high-spend post shows 0 comments / got skipped
Likely a **dark (unpublished) ad post**. Facebook often consolidates engagement from many same-creative dark posts onto a canonical post, so the per-post thread is genuinely empty. Nothing to pull — this is expected and safe.

### R2 FAIL / gallery built but no URL
- Keys wrong or bucket not public. Re-check docs/02. The bucket must have **public access** (custom domain or r2.dev) and the API token must be **Object Read & Write**.
- `R2_PUBLIC_BASE` must be the **public** URL (your custom domain or `https://pub-xxxx.r2.dev`), **not** the S3 endpoint.

### "View on Facebook" link says content isn't available
Expected for **dark/unpublished** posts or deleted posts — Facebook only serves public permalinks. Most published posts link fine.

### Images don't load in the gallery
Facebook CDN links expire, which is *why* the kit mirrors to R2. If an image is missing, the original likely expired before mirroring, or R2 upload failed (check the run log for `R2 mirror failed`). Re-run `intel pull --fresh` for that period to re-mirror.

### boto3 not found
`pip install -r requirements.txt` (or `pip install boto3`).

---

Still stuck? Open an issue on the repo with the `intel doctor` output (redact your token) and the exact command + error.
