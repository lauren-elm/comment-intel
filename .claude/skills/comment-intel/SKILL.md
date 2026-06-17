---
name: comment-intel
description: Rank a Facebook ad account's top-spending and positive-ROI posts over a window, scrape every comment + reply (read-only), mirror media to Cloudflare R2, and publish a searchable white-label gallery. Use when the user says "pull the ad comments", "comment intel", "scrape comments off my best ads", "build the comment gallery", or wants voice-of-customer mining from Facebook ad posts. Wraps the ad-comment-intel CLI.
---

# Comment Intel

A thin wrapper around the **ad-comment-intel** CLI. The Python package does the work; this skill just drives it from Claude Code.

## Before running
1. Confirm onboarding is done: a `config.env` exists in the project folder. If not, tell the user to run `python -m intel setup` (it needs their Meta token + Cloudflare R2 keys — see `docs/01-create-meta-app.md` and `docs/02-cloudflare-r2.md`).
2. Always run the pre-flight check first:
   ```
   python -m intel doctor
   ```
   If anything is **[FAIL]**, stop and help the user fix that connection before continuing.

## The run
Run end-to-end (long-running for big accounts — it's resumable):
```
python -m intel run
```
Or stage by stage: `python -m intel rank` → review `output/posts_*.csv` → `python -m intel pull` → `python -m intel gallery`.

Useful flags: `--rank-only` (spend/ROI report only), `--no-replies` (faster), `--no-upload` (local gallery), `--fresh` (re-scrape).

## If it stops or rate-limits
Just run `python -m intel run` again — ranking is cached and comment scraping skips posts already done. Don't start over.

## When done, report
- Posts ranked, positive-ROI count, posts selected.
- Comment totals (comments / replies / photos / videos) from the run's TOTALS block.
- The shareable gallery URL.

## Guardrails (carry every time)
- **Read-only on Facebook.** Never add reply/hide/delete behavior.
- Commenter identity is privacy-locked — **not a lead list**.
- The gallery is **public** and may contain **customer emails/photos** — keep the link internal; don't post it publicly.
- ROI is **FB-attributed** (`omni_purchase` value ÷ spend) — a directional indicator, not last-touch funnel truth.
