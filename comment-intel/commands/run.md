---
description: Run Comment Intel end-to-end — rank the ad account's top-spending and positive-ROI posts over the configured window, scrape every comment + reply (read-only), mirror media to Cloudflare R2, and publish the searchable gallery. Resumable.
---

# Comment Intel — Run

You are running the **Comment Intel** pipeline. Use the **comment-intel** skill (read its `SKILL.md`).

## Pre-flight
1. `ls ~/comment-intel/config.env 2>/dev/null` — if missing, the user hasn't onboarded; send them to `/comment-intel:setup` and stop.
2. Always verify first:
   ```bash
   export INTEL_CONFIG="$HOME/comment-intel/config.env"
   python "$CLAUDE_PLUGIN_ROOT/skills/comment-intel/scripts/comment_intel.py" doctor
   ```
   If anything is **[FAIL]**, fix it (see `references/04-troubleshooting.md`) before continuing.

## Run
```bash
export INTEL_CONFIG="$HOME/comment-intel/config.env"
python "$CLAUDE_PLUGIN_ROOT/skills/comment-intel/scripts/comment_intel.py" run
```
- **Long-running** for big accounts — run it in the background (`run_in_background`) and report when it finishes.
- **Resumable** — if it stops or rate-limits, run the same command again. Ranking is cached; already-scraped posts are skipped. Do **not** start over.
- Faster/partial options: `--rank-only` (just the spend/ROI CSVs), `--no-replies`, `--no-upload`, `--fresh`.

## Report when done
- Window analyzed, posts ranked, positive-ROI count, posts selected.
- Totals from `=== TOTALS ===` (comments / replies / photos / videos / skipped).
- The shareable gallery URL.

**Guardrails:** read-only on Facebook; identity privacy-locked (not a lead list); the gallery is public + may contain customer emails — keep the link internal.
