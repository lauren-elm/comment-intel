# 🧑‍🏫 Workshop: Build a Searchable Ad-Comment Gallery in ~20 Minutes

New to Claude Code? Perfect. By the end of this you'll have installed a plugin, run a couple of commands, and produced a real, shareable tool — a searchable gallery of every comment on your best Facebook ads.

**Here's what you're building** (a finished example):
👉 https://files.elmdirt.com/comments/_gallery/elm-dirt-demo-comment-gallery.html

Nothing here writes to Facebook — it only *reads* your comments. Your data stays on your own accounts.

---

## ✅ Before you start (5 min)

You need three things, all free:

1. **Claude Code** installed and open. (If you can read this in it, you're good.)
2. **A Facebook ad account you manage** — and admin access to the Business that owns it.
3. **A Cloudflare account** — sign up free at https://dash.cloudflare.com (this hosts your gallery).

That's it. You'll grab two access keys during setup; we'll walk you through both.

---

## Step 1 — Install the plugin (2 min)

In Claude Code, type these two lines:

```
/plugin marketplace add lauren-elm/comment-intel
/plugin install comment-intel
```

That's the whole install. You now have two new commands: `/comment-intel:setup` and `/comment-intel:run`.

> 💡 **What just happened:** a *plugin* is a bundle Claude Code can load. This one added *slash commands* (the `/...` shortcuts) and a *skill* (instructions Claude follows). You didn't install any programming tools — it's self-contained.

---

## Step 2 — Connect your accounts (10 min)

Type:

```
/comment-intel:setup
```

Claude will walk you through it conversationally. You'll need to paste two things:

### 2a. Your Facebook token (the fast workshop way)

For the workshop we use a quick token that's good for ~1–2 hours — plenty to get a result today. (You can switch to a permanent one later; see *Going further*.)

1. Go to **https://developers.facebook.com/tools/explorer**
2. Top right: pick (or create) an app — any app is fine. If you have none, click **Create App → Other → Business**, name it, done.
3. Click **Add a Permission** and tick these four: `ads_read`, `read_insights`, `pages_show_list`, `pages_read_user_content`.
4. Click **Generate Access Token** and approve the popups (choose your ad account + Page when asked).
5. **Copy the long token string** and paste it to Claude when it asks.

Claude will then show you your ad accounts and Pages as a list — just pick the right ones.

### 2b. Your Cloudflare R2 (free hosting)

1. In Cloudflare, left sidebar → **R2** → **Create bucket** → name it `comment-intel` → Create. Copy your **Account ID** (shown on the R2 page).
2. **Manage R2 API Tokens** → **Create API token** → permission **Object Read & Write** → Create. Copy the **Access Key ID** and **Secret Access Key**.
3. Bucket → **Settings → Public access → R2.dev subdomain → Allow Access.** Copy the `https://pub-xxxx.r2.dev` URL.
4. Paste those to Claude when asked. (The setup fills in the rest for you.)

> 💡 The full step-by-step lives in the plugin's `references/01-create-meta-app.md` and `references/02-cloudflare-r2.md` — Claude can open these and read them to you anytime. Just ask.

### 2c. Verify

When setup finishes, Claude runs a check. You want all green:

```
[PASS] Meta token
[PASS] Ad account
[PASS] Page token
[PASS] Cloudflare R2
```

Anything red? Just tell Claude what it says — it'll help you fix it.

---

## Step 3 — Run it (Claude does the work)

```
/comment-intel:run
```

Claude now: finds your top-spending and most profitable ad posts, reads every comment + reply, saves the photos/videos people posted, and builds your gallery. On a big account this can take a while — that's normal. It's safe to let it run.

When it's done, Claude gives you a **link**. Open it. 🎉

You can:
- **Search** any word (press Enter)
- Filter to **Photos / Videos**, or **🔴 complaints / ❓ questions / 🟢 positive**
- Click **"View on Facebook"** on any comment to jump to it live

There's also a **CSV** (`…-comments.csv`) if you'd rather pull the raw data into a spreadsheet.

---

## 🆘 If you get stuck

| Problem | Fix |
|---|---|
| "No config found" | Run `/comment-intel:setup` first. |
| Token error / "expired" | The workshop token lasts ~1–2 hrs. Grab a fresh one (Step 2a) and re-run setup. |
| Ad account "FAIL" | Make sure you picked the right account and your token has `ads_read`. |
| R2 "FAIL" / no link | Re-check the bucket is **public** (Step 2b.3) and the token is **Read & Write**. |
| Anything else | Paste the error to Claude — seriously, it's good at this. |

---

## 🎓 What you just learned (Claude Code concepts)

- **Plugins** — installable bundles that add new powers (`/plugin install …`).
- **Slash commands** — `/comment-intel:setup` and `:run` are shortcuts the plugin added.
- **Skills** — the instructions Claude follows behind the scenes to drive the tool.
- **Talking vs. typing** — you didn't memorize commands; you answered questions. That's the whole idea.

---

## 🚀 Going further

- **Make your token permanent:** the quick token expires. For ongoing use, create a **System User token** in Meta Business Settings (no re-doing it every time) — see `references/01-create-meta-app.md`, section C. Then run `/comment-intel:setup` again to update it.
- **Tune the window:** want 6 months instead of 13, or a higher spend cutoff? Just ask Claude to change the settings (or edit `~/comment-intel/config.env`).
- **Re-run anytime:** `/comment-intel:run` is resumable and cached — run it again whenever you want fresh comments.

Have fun. 🌱
