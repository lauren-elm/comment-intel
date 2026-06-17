---
description: First-time setup for Comment Intel. Guides the user through creating a Meta app + read-only token (ad account + Page), a free Cloudflare R2 bucket for hosting, then validates the connection. Run once per brand/workstation.
---

# Comment Intel — Setup

You are running first-time onboarding for **Comment Intel**. The user just installed the plugin and wants to connect their Facebook ad account and Cloudflare R2 so they can mine ad-post comments.

Use the **comment-intel** skill — read its `SKILL.md` and the `references/01-create-meta-app.md` and `references/02-cloudflare-r2.md` guides, then walk the user through them. Prefer `AskUserQuestion` for any choice; never make them type when they could click.

## Flow

1. **Detect existing setup** — `ls ~/comment-intel/config.env 2>/dev/null`. If it exists, summarize the config (key names only, never values), and offer to re-run setup (overwrites) or just verify (`doctor`). Default to verify.

2. **Meta app + token** — walk them through `references/01-create-meta-app.md`: create a Meta app, generate a **System User** access token, assign their **ad account** + **Page**, and grant `ads_read`, `read_insights`, `pages_show_list`, `pages_read_user_content`. This is read-only — reassure them nothing posts to Facebook.

3. **Cloudflare R2** — walk them through `references/02-cloudflare-r2.md`: a free bucket, an **Object Read & Write** API token, and a public URL (custom domain or r2.dev).

4. **Write config + pick assets** — run the wizard, which validates the token and lists their ad accounts + Pages to choose from:
   ```bash
   export INTEL_CONFIG="$HOME/comment-intel/config.env"
   python "$CLAUDE_PLUGIN_ROOT/skills/comment-intel/scripts/comment_intel.py" setup
   ```
   (If interactive prompts won't work in this context, collect the values via `AskUserQuestion` and write `~/comment-intel/config.env` yourself from `scripts/config.example.env`.)

5. **Verify** — `python "$CLAUDE_PLUGIN_ROOT/skills/comment-intel/scripts/comment_intel.py" doctor` (with `INTEL_CONFIG` exported). Every line must be **[PASS]**; fix FAILs via `references/04-troubleshooting.md`.

When all green, tell them they're ready: run `/comment-intel:run`.

**Guardrails:** read-only on Facebook; commenter identity is privacy-locked (not a lead list); each brand uses its own token + R2.
