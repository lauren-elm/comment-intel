# 🛰️ Ad Comment Intel

**Turn your best Facebook ads' comment sections into a searchable goldmine of voice-of-customer intel.**

This kit finds your **highest-spending and most profitable ad posts** over any window, scrapes **every comment + reply** off them (read-only), mirrors the attached **photos and videos** to your own cloud, and publishes a **searchable, filterable gallery** you can share with a link.

It's **white-label** and **self-serve** — you bring your own Meta app, ad account, and a free Cloudflare R2 bucket. Your data stays on your infrastructure.

```
┌─────────┐   ┌──────────┐   ┌──────────────┐   ┌─────────────────┐
│  rank   │ → │   pull   │ → │   gallery    │ → │  share the URL  │
│ spend + │   │ comments │   │  search +    │   │  files.you.com/ │
│  ROI    │   │ + media  │   │  filters     │   │  …gallery.html  │
└─────────┘   └──────────┘   └──────────────┘   └─────────────────┘
```

---

## What you get

- **Smart targeting** — ranks ad *posts* (not just ads) by total spend and FB-attributed ROAS, then pulls the union of your **positive-ROI** posts and your **top spenders**. The biggest, most relevant pool — not random ads.
- **Complete comment capture** — every top-level comment *and* reply thread, with likes, dates, and a light auto-classification (🔴 complaint / ❓ question / 🟢 positive / ⚪ other).
- **Durable media** — photos and videos customers attached are copied to your R2 (Facebook's CDN links expire; yours won't).
- **A gallery people actually use** — press-Enter search over the comment text, filter by Photos / Videos / category, and a one-click **"View on Facebook"** deep link on every card that jumps to the live comment.
- **Resumable + rate-limit-safe** — monthly spend pulls are cached; comment scraping skips what's already done.

> **Read-only.** This tool never writes to Facebook — no replies, hides, or bans.

---

## Quick start

```bash
# 1. Install (Python 3.9+)
pip install -r requirements.txt        # or: pip install .

# 2. Onboard — connect Meta + Cloudflare (interactive)
python -m intel setup

# 3. Verify everything connects
python -m intel doctor

# 4. Go — rank, scrape, publish
python -m intel run
```

When it finishes you'll get a **shareable gallery URL**. That's it.

> If you ran `pip install .`, you can use the shorter `intel setup` / `intel run` instead of `python -m intel …`.

---

## Setup guides (do these once)

1. **[Create your Meta app + token](docs/01-create-meta-app.md)** — make a Facebook app, connect your ad account + Page, grant the read permissions, and get a long-lived token.
2. **[Set up Cloudflare R2](docs/02-cloudflare-r2.md)** — a free bucket + public domain to host the gallery and media.
3. **[Usage & the flow](docs/03-usage.md)** — commands, the window/threshold settings, and how the ranking works.
4. **[Troubleshooting](docs/04-troubleshooting.md)** — rate limits, dark posts, common errors.

---

## Commands

| Command | What it does |
|---|---|
| `intel setup` | Interactive onboarding → writes `config.env` |
| `intel doctor` | Verifies Meta token, ad account, Page token, and R2 |
| `intel rank` | Ranks posts by spend + ROI → `output/posts_*.csv` + `post_list.txt` |
| `intel pull` | Scrapes comments for the selected posts → `output/comment_store/` |
| `intel gallery` | Builds + uploads the searchable gallery |
| `intel run` | All of the above, end to end |

Useful flags: `intel run --rank-only` (just the spend/ROI report), `--no-replies` (faster), `--no-upload` (build gallery locally), `--fresh` (re-scrape posts already done).

---

## Outputs

```
output/
├── posts_by_spend.csv        # every post ranked by spend (+ revenue, ROAS)
├── posts_positive_roi.csv    # the positive-ROI cut
├── post_list.txt             # the posts selected for comment scraping
├── comment_store/            # one JSON per post: comments, replies, media, categories
└── comment-gallery.html      # local copy of the gallery (also uploaded to R2)
```

---

## Important caveats

- **Commenter identity is privacy-locked.** Facebook returns no name/ID for regular commenters. This is voice-of-customer *content*, not a lead list.
- **The gallery is public** (anyone with the unguessable URL can view it) and **may contain customer-posted emails/photos.** Keep the link internal; don't index it publicly.
- **ROI = FB-attributed** (`omni_purchase` value ÷ spend). It's a strong *directional* indicator, not last-touch funnel truth.
- **Dark/unpublished ad posts** sometimes report zero comments (engagement is consolidated elsewhere) — they're skipped automatically.

MIT licensed. Built to be gifted. 🌱
