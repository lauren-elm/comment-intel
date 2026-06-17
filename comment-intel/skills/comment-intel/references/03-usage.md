# 3 · Usage & the flow

Once `intel doctor` is all green, you're ready.

```bash
python comment_intel.py run
```

That runs the whole pipeline. Here's what each stage does and how to tune it.

---

## The flow

### 1. Rank (`intel rank`)
Pulls **ad-level spend + revenue** month by month over your window (`MONTHS_BACK`), aggregates it **per underlying post** (one post usually backs many ads), and computes FB-attributed **ROAS** (`omni_purchase` value ÷ spend).

It writes:
- `output/posts_by_spend.csv` — every post, ranked by spend, with revenue + ROAS.
- `output/posts_positive_roi.csv` — posts with **spend ≥ `MIN_SPEND`** and **ROAS > `MIN_ROAS`**.
- `output/post_list.txt` — the posts selected for comment scraping: **the positive-ROI cut ∪ the top `TOP_BY_SPEND` spenders**. This is the "biggest, most relevant pool."

Monthly pulls are **cached** in `output/cache/`. Re-runs only re-pull the current (incomplete) month, so they're fast and won't trip rate limits. Delete a file in `cache/` to force a re-pull.

### 2. Pull (`intel pull`)
For each selected post, scrapes **all comments + reply threads** (read-only), classifies each, and mirrors photos/videos to your R2. Writes one JSON per post to `output/comment_store/`.

- **Resumable:** posts already scraped are skipped. If a run is interrupted or rate-limited, just run it again.
- Posts that report **0 comments** (often dark/unpublished ad posts) are skipped automatically.

### 3. Gallery (`intel gallery`)
Builds the searchable HTML from everything in `comment_store/` and uploads it to R2. Prints the **shareable URL**.

The gallery has: press-Enter **search**, **Photos / Videos / Has-media** filters, **category** filters (complaint/question/positive), and a **"View on Facebook"** deep link per card.

It also writes a **flat data export** — `output/comments_export.csv` (one row per comment: post_id, comment_id, category, likes, date, media_url, facebook_link, text) — and uploads it next to the gallery as `…-comments.csv`. That's the machine-readable file to pull into a spreadsheet, a script, or another tool, instead of the visual page.

---

## Settings (`config.env`)

| Key | Default | Meaning |
|---|---|---|
| `MONTHS_BACK` | `13` | How many months of spend to analyze (includes current month) |
| `MIN_SPEND` | `300` | A post needs at least this much total spend to count |
| `MIN_ROAS` | `1.0` | "Positive ROI" = ROAS strictly above this |
| `TOP_BY_SPEND` | `20` | Always also include the top-N spenders (even if unprofitable) |
| `MIN_COMMENTS` | `1` | Skip posts with fewer than this many comments |
| `MAX_PER_POST` | `2000` | Cap comments pulled per post (huge threads) |
| `BRAND_NAME` | — | Gallery title |

Change a value, re-run `intel run`. Ranking re-reads from cache, so it's quick.

---

## Common variations

```bash
# Just the spend/ROI report, no scraping:
python comment_intel.py run --rank-only

# Faster scrape (skip reply threads):
python comment_intel.py run --no-replies

# Build the gallery locally without uploading:
python comment_intel.py gallery --no-upload

# Re-scrape everything from scratch (ignore what's already pulled):
python comment_intel.py pull --fresh

# Analyze a longer history:
#   set MONTHS_BACK=24 in config.env, then:
python comment_intel.py run
```

---

## How long does it take?

- **Rank:** seconds to a couple minutes (cached after first run).
- **Pull:** depends on how many posts and how chatty they are. High-volume posts (1,000+ comments + media) take a while; budget anywhere from minutes to an hour+ for a big account. It's resumable, so you can stop and continue.
- **Gallery:** seconds.

➡️ Hitting an error? **[Troubleshooting](04-troubleshooting.md)**
