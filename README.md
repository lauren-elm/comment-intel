# 🛰️ Comment Intel — a Claude Code plugin

**Turn any brand's best Facebook ads' comment sections into a searchable goldmine of voice-of-customer intel — all inside Claude Code.**

Comment Intel finds an ad account's **highest-spending and most profitable posts** over any window, scrapes **every comment + reply** off them (read-only), mirrors the attached **photos and videos** to your own Cloudflare R2, and publishes a **searchable, filterable gallery** you can share with a link.

It's **white-label** and **self-serve** — each person brings their own Meta app, ad account, and a free Cloudflare R2 bucket. Pure Python standard library: **nothing to `pip install`.**

```
/comment-intel:setup   →   /comment-intel:run   →   shareable gallery URL
   (guided onboarding)       (rank → scrape → publish)
```

---

## Install (in Claude Code)

Add the marketplace, then install the plugin:

```
/plugin marketplace add lauren-elm/comment-intel
/plugin install comment-intel
```

> The repo must be **public** for others to install this way. You can also point at a local path while testing: `/plugin marketplace add /path/to/comment-intel`.

That gives everyone two slash commands:

| Command | What it does |
|---|---|
| **`/comment-intel:setup`** | Guided onboarding — create a Meta app + read-only token, connect the ad account + Page, set up a free Cloudflare R2 bucket, and verify the connection. |
| **`/comment-intel:run`** | Rank top-spending + positive-ROI posts → scrape comments → publish the searchable gallery. |

You can also just talk to it: *"set up comment intel"* / *"pull the comments off my best ads."*

---

## What it does

- **Smart targeting** — ranks ad *posts* (not just ads) by total spend and FB-attributed ROAS, then pulls the union of **positive-ROI** posts and **top spenders**. The biggest, most relevant pool.
- **Complete capture** — every top-level comment *and* reply, with likes, dates, and auto-classification (🔴 complaint / ❓ question / 🟢 positive / ⚪ other).
- **Durable media** — customer photos/videos copied to your R2 (Facebook's CDN links expire; yours won't).
- **A gallery people use** — press-Enter search, Photos / Videos / category filters, and a **"View on Facebook"** deep link per comment.
- **Resumable + rate-limit-safe** — cached spend pulls; scraping skips what's done.

> **Read-only.** Never writes to Facebook — no replies, hides, or bans.

---

## First-time setup (what each person needs)

Two external accounts, ~25 minutes once. The `/comment-intel:setup` command walks them through both:

1. **A Meta app + read-only token** → `comment-intel/skills/comment-intel/references/01-create-meta-app.md`
2. **A free Cloudflare R2 bucket** → `comment-intel/skills/comment-intel/references/02-cloudflare-r2.md`

State lives in a per-user workspace: `~/comment-intel/config.env` (connection) and `~/comment-intel/output/` (CSVs, comment data, local gallery copy).

---

## Run it as a plain script (optional, no Claude Code)

Everything is a normal Python program if you ever want it outside Claude Code:

```bash
cd comment-intel/skills/comment-intel/scripts
python comment_intel.py setup      # onboarding wizard
python comment_intel.py doctor     # verify connections
python comment_intel.py run        # rank → scrape → publish
```

No dependencies — Python 3.9+ only.

---

## Repo layout

```
.claude-plugin/marketplace.json          # marketplace manifest
comment-intel/
├── .claude-plugin/plugin.json           # plugin manifest
├── commands/
│   ├── setup.md                         # /comment-intel:setup
│   └── run.md                           # /comment-intel:run
└── skills/comment-intel/
    ├── SKILL.md                         # how Claude drives it
    ├── references/                      # the setup + usage guides
    └── scripts/
        ├── comment_intel.py             # launcher (python comment_intel.py …)
        ├── config.example.env
        └── intel/                       # the engine (pure stdlib)
```

---

## Important caveats

- **Commenter identity is privacy-locked.** Facebook returns no name/ID for regular commenters — voice-of-customer *content*, not a lead list.
- **The gallery is public** (unguessable URL) and **may contain customer-posted emails/photos.** Keep the link internal.
- **ROI = FB-attributed** (`omni_purchase` value ÷ spend) — a directional indicator, not last-touch funnel truth.
- **Each brand uses its own** Meta app + R2. Never mix tokens or buckets.

MIT licensed. Built to be gifted. 🌱
