# neopets-auto-helper

This project uses Python Playwright to achieve asynchronous operations for completing tasks on Neopets.

# How to config my neopets accounts

Each account lives in its own JSON file — **one account per file** — so every run is
fully isolated. Start from the template `account.example.json`:

- Set `LEGACY` to `true` for a classic account, then fill `USERNAME` / `PASSWORD`.
- Set `LEGACY` to `false` for a NeoPass (SSO) account: put the NeoPass email/password in
  `USERNAME` / `PASSWORD`, and the in-game Neopets name in `NEOPASS_USERNAME`.
- Each `*_FLAG` toggles a daily task for that account.
- Pick where run results are sent with `NOTIFY_METHOD` (`"gmail"`, `"telegram"`, or
  `"both"`) and fill the matching `GMAIL_NOTIFY` / `TELEGRAM_NOTIFY` block — see
  [Notify](#notify) below.

Make one such file per account (e.g. `my_account.json`); keep it out of git.

# How to run

`main.py` runs the **single** account selected by the `ACCOUNT_FILE` env var, then exits —
exit code `0` on success, non-zero if login failed. `ACCOUNT_FILE` defaults to `account.json`
when unset. Cookies persist in `sessions/`, but the run keeps **no** cooldown state, so every
run attempts all enabled tasks (timing is controlled entirely by your scheduler).

```
# source venv...
pip install -r requirements.txt
ACCOUNT_FILE=my_account.json python main.py
```

> The old "loop forever over every account" behaviour is gone; scheduling is now external
> (see the Scheduling section below). Each run is stateless — the `time/` cooldown file is no
> longer read or written.

# Build Docker images

The image no longer bakes in credentials or state — mount your account JSON (and, if you
want to reuse cookies, `sessions/`) at run time.

```
x86
docker buildx build --load --platform linux/amd64 -t neopets-playwright-helper-x86:latest .
docker save -o neopets-playwright-helper-x86.tar neopets-playwright-helper-x86:latest

arm64
docker buildx build --load --platform linux/arm64 -t neopets-playwright-helper-arm64:latest .
docker save -o neopets-playwright-helper-arm64.tar neopets-playwright-helper-arm64:latest
```

Run one account in a throwaway container — just mount your single-account JSON and point
`ACCOUNT_FILE` at it (absolute path, so you don't need to know the container's workdir):

```
docker run --rm \
  -v "/path/to/my_account.json:/data/account.json:ro" \
  -e ACCOUNT_FILE=/data/account.json \
  neopets-playwright-helper-x86:latest
```

The bot keeps **no cooldown state** — every run is a clean environment and attempts all
enabled tasks. The only thing worth persisting is cookies (fewer re-logins, which helps the
flaky NeoPass login). To reuse them, also mount `sessions/` (it lives under the base image's
workdir `/usr/src/app` — confirm with
`docker run --rm --entrypoint pwd neopets-playwright-helper-x86:latest`):

```
docker run --rm \
  -v "/path/to/my_account.json:/data/account.json:ro" \
  -v "$PWD/sessions:/usr/src/app/sessions" \
  -e ACCOUNT_FILE=/data/account.json \
  neopets-playwright-helper-x86:latest
```

Want a 100% clean run with no cookie reuse either? Just omit the `sessions/` mount — the
first `docker run` example above already does exactly that.

# Scheduling

The container runs one account then exits (exit code `0` = ok, non-zero = login failed),
so schedule it with whatever you already use — cron, systemd timers, or n8n — by running
the `docker run` command above (one per account) on a timer. Each run gets a fresh
container/browser, so accounts no longer interfere with each other.

## Windows: run every account with one command

`run_all_accounts.bat` (in the repo root) loops over every `*.json` in an `accounts\` folder
and runs one throwaway container per account, **sequentially** (never overlapping), staggering
them so logins are spread out. Cookies are reused via the `sessions\` folder. Point Windows
Task Scheduler at it to run all your accounts on a timer.

- Put one single-account JSON per account in `accounts\` (e.g. `accounts\alice.json`).
- Edit the `IMAGE` and `STAGGER` (seconds between accounts) variables at the top of the
  `.bat` if needed.
- Docker Desktop must be running; the script mounts `accounts\` (read-only) and `sessions\`.
- Keep a log with `run_all_accounts.bat >> run.log 2>&1`.

# Inclouded Features

- Bank Collect
- Fishing
- Fruit
- Jelly
- Omelette
- Springs
- Trudys
- Shrine
- Tombola
- Tdmbgpop
- Advent Calendar
- The Void Within Event
    - Hosiptal
    - Void Location
- Buy Stocks / Sell Stocks (60 NP)
- PetLab    # First, You need to collect map to open.
- PetpetLab # First, You need to collect map to open.
- Shop Wizard
- Training School (Strength, Defence, Agility, Endurance and Level)
    - Cap'n Threelegs' Swashbuckling Academy
    - Mystery Island Training School
    - Secret Ninja Training School # Level 250 up
  
# Coming Features

- Battledome
- Daily Quests

# Notify

Each run sends a summary (or a login-failure alert) through one or more notification
channels. Pick the channel(s) with `NOTIFY_METHOD` in the account JSON:

- `"gmail"` — send via Gmail (default).
- `"telegram"` — send via a Telegram bot.
- `"both"` (or `"all"`, or a list like `["gmail", "telegram"]`) — send via both.

A channel is skipped automatically if its config block is empty, so you only need to fill
in the one(s) you actually use.

## Gmail

Uses the traditional Gmail sending mode and requires an app token from Google services:

```json
"NOTIFY_METHOD": "gmail",
"GMAIL_NOTIFY": {
    "APPLICATION_TOKEN": "your-gmail-app-token",
    "SENDER_GMAIL": "you@gmail.com",
    "RECEIVER_EMAIL": "you@gmail.com"
}
```

## Telegram

1. Create a bot with [@BotFather](https://t.me/BotFather) to get a `BOT_TOKEN`.
2. Open your bot in Telegram and send it any message (e.g. `hi`) — the bot cannot message
   you until you start a chat with it.
3. Get your `CHAT_ID`: open
   `https://api.telegram.org/bot<BOT_TOKEN>/getUpdates` and read `result[].message.chat.id`.

```json
"NOTIFY_METHOD": "telegram",
"TELEGRAM_NOTIFY": {
    "BOT_TOKEN": "123456:ABC-DEF...",
    "CHAT_ID": "123456789"
}
```

> **`CHAT_ID` is _your_ chat id, not the bot's.** It's the `chat.id` from `getUpdates`
> (your personal user id, or a group id). It is **not** the number before the colon in the
> `BOT_TOKEN` — that's the bot's own id, and a bot can't send messages to itself.