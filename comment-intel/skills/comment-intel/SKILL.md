---
name: comment-intel
description: Mine Facebook ad-post comments for any brand. Rank an ad account's top-spending and positive-ROI posts over a window, scrape every comment + reply (read-only), mirror photos/videos to Cloudflare R2, and publish a searchable gallery. Use when the user says "comment intel", "pull the ad comments", "scrape comments off my best ads", "build a comment gallery", "voice of customer from Facebook ads", or runs /comment-intel:setup or /comment-intel:run. Drives a bundled pure-stdlib Python engine — no pip install.
---

# Comment Intel

Connect a brand's own Meta ad account + Facebook Page (read-only) and a free Cloudflare R2 bucket, then turn their best ads' comment sections into a searchable voice-of-customer gallery.

The engine is bundled at `${CLAUDE_PLUGIN_ROOT}/skills/comment-intel/scripts/comment_intel.py` (pure Python standard library — nothing to install). Drive it with the Bash tool. **All state lives in a stable workspace** so it works no matter where the user is:

```
WORKSPACE = ~/comment-intel
CONFIG    = ~/comment-intel/config.env     (created by setup)
OUTPUT    = ~/comment-intel/output         (CSVs, comment_store, local gallery)
```

Always run the engine with the workspace pinned via env vars:

```bash
PY="$CLAUDE_PLUGIN_ROOT/skills/comment-intel/scripts/comment_intel.py"
export INTEL_CONFIG="$HOME/comment-intel/config.env"
python "$PY" <command>
```

(If `$CLAUDE_PLUGIN_ROOT` is unset, fall back to `~/.claude/plugins/cache/comment-intel/comment-intel`. Use `python` or `python3`, whichever exists.)

## Decide what the user wants
- **First time / "set it up" / not connected yet** → run the **Setup** flow below (or tell them to use `/comment-intel:setup`).
- **Already onboarded / "run it" / "pull comments"** → run the **Run** flow.
- Check state first: `ls ~/comment-intel/config.env 2>/dev/null`. If missing → Setup. If present → Run.

## Setup (onboarding)
The goal is a complete `config.env` + a passing `doctor`. The two things the user must obtain are external; walk them through it conversationally and use `AskUserQuestion` for choices.

1. **Meta app + token.** Walk them through `references/01-create-meta-app.md`: create a Meta app, make a System User token, assign the ad account + Page, grant `ads_read`, `read_insights`, `pages_show_list`, `pages_read_user_content`. Have them paste the token.
2. **Cloudflare R2.** Walk them through `references/02-cloudflare-r2.md`: free bucket, Object Read & Write API token, and a public URL (custom domain or r2.dev).
3. Run the wizard, which validates the token, lists their ad accounts + Pages to pick, and writes the config:
   ```bash
   export INTEL_CONFIG="$HOME/comment-intel/config.env"
   python "$PY" setup
   ```
   The wizard uses interactive prompts. If running it non-interactively is a problem, instead collect the values yourself via `AskUserQuestion`/chat and write `config.env` from `scripts/config.example.env` (same keys), then continue.
4. Verify:
   ```bash
   python "$PY" doctor
   ```
   Every line must be **[PASS]**. Fix any **[FAIL]** using `references/04-troubleshooting.md` before running.

## Run
```bash
export INTEL_CONFIG="$HOME/comment-intel/config.env"
python "$PY" run
```
This ranks posts → selects top spenders + positive ROI → scrapes comments → builds + uploads the gallery. It is **long-running** for big accounts and **resumable** — if it stops or rate-limits, run the same command again (ranking is cached; scraped posts are skipped). Run it in the background (`run_in_background`) for large accounts and report when done.

Stage-by-stage if preferred: `rank` (writes `output/posts_*.csv`) → review → `pull` → `gallery`.
Flags: `--rank-only`, `--no-replies` (faster), `--no-upload` (local only), `--fresh` (re-scrape).

## When done, report
- Window analyzed, posts ranked, positive-ROI count, posts selected.
- Comment totals from the run's `=== TOTALS ===` block (comments / replies / photos / videos).
- The shareable gallery URL (the `CLOUD URL:` / `Shareable gallery:` line).

## Guardrails — carry every time
- **Read-only on Facebook.** Never add reply / hide / delete behavior. Never edit the engine to write to Facebook.
- Commenter identity is **privacy-locked** — voice-of-customer content, **not a lead list**.
- The gallery is **public** (unguessable URL) and may contain **customer emails/photos** — keep the link internal; do not index it publicly.
- ROI is **FB-attributed** (`omni_purchase` value ÷ spend) — a directional indicator, not last-touch funnel truth.
- Each user runs on **their own** Meta app + R2. Never mix brands' tokens or buckets.

## References (read as needed)
- `references/01-create-meta-app.md` — Meta app, token, permissions, connect ad account + Page
- `references/02-cloudflare-r2.md` — free R2 bucket + public hosting
- `references/03-usage.md` — the flow, settings, variations
- `references/04-troubleshooting.md` — rate limits, dark posts, common errors
