# 1 · Create your Meta app & get a token

You need a **long-lived access token** that can (a) read your ad account's spend and (b) read your Page's comments. The most reliable way is a **System User token** in Meta Business Manager — it doesn't expire every hour.

Time: ~15 minutes, once.

---

## A. Prerequisites

- You're an **admin** of the **Business Manager** that owns the ad account and the Facebook Page.
- The ad account and the Page are both inside that Business (Business Settings → Accounts).

---

## B. Create a Meta app

1. Go to **https://developers.facebook.com/apps** → **Create app**.
2. Choose use case **Other** → type **Business** → name it (e.g. "Comment Intel") and pick your Business.
3. In the app, open **App settings → Basic**. Note the **App ID** and **App Secret** (you generally won't need them for a System User token, but keep them handy).
4. Add the **Marketing API** product (left sidebar → "Add product"). This makes ads/insights available.

> You do **not** need to submit the app for App Review for your **own** assets. Standard Access is enough to read your own ad account and Page.

---

## C. Make a System User token (recommended — never expires)

1. Go to **Business Settings** → **Users → System Users** → **Add**.
2. Create one named e.g. "comment-intel-bot", role **Admin** (or Employee).
3. Click **Add Assets** and assign:
   - Your **ad account** → enable **View Performance** (read) — "Manage" is fine too.
   - Your **Page** → enable **everything / Manage** (so it can read comments).
4. Click **Generate new token**. Pick your app. Select these permissions:
   - `ads_read`
   - `read_insights`
   - `pages_show_list`
   - `pages_read_user_content`
   - *(optional, only if your ads run on Instagram and you want IG comments later: `instagram_basic`, `instagram_manage_comments`)*
5. **Copy the token now** and keep it somewhere safe — you can't see it again. This is your `META_ACCESS_TOKEN`.

> **Alternative (quick test, expires in ~1–2 hours):** Graph API Explorer (developers.facebook.com/tools/explorer) → pick your app → add the scopes above → Generate Access Token. Fine for a first run; use the System User token for anything ongoing.

---

## D. Find your ad account id

- **Ads Manager** → top-left account dropdown → the number under the account name, like `act_1234567890`.
- In `config.env`, enter **just the digits** (`1234567890`) — the kit adds `act_` for you. The setup wizard lists your accounts so you can just pick one.

---

## E. Find your Page id

- Your Page → **About**, or **Business Settings → Accounts → Pages**.
- The setup wizard lists your Pages so you can pick — you usually won't need to look this up.

---

## F. Plug it in

Run the wizard and paste the token when asked:

```bash
python -m intel setup
```

It validates the token, lists your ad accounts and Pages to pick from, and writes everything to `config.env`. Then:

```bash
python -m intel doctor
```

should show **[PASS]** for the Meta token, ad account, and Page token.

➡️ Next: **[Set up Cloudflare R2](02-cloudflare-r2.md)**
