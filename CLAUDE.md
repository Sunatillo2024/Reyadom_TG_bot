# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```sh
# Environment
python3.11 -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements-dev.txt

# Database (Docker)
docker compose up -d postgres                           # PostgreSQL on host port 55432
docker compose exec -T postgres createdb -U postgres ryadom_bot_test

# Run
alembic upgrade head                                   # must run before starting the bot
python -m bot.main

# Lint / schema check
ruff check .
DATABASE_URL=postgresql+asyncpg://postgres:1212@localhost:55432/ryadom_bot alembic check

# Tests (requires a live Postgres database)
TEST_DATABASE_URL=postgresql+asyncpg://postgres:1212@localhost:55432/ryadom_bot_test pytest
```

Run only **one** polling process per bot token. Two simultaneous instances cause a `TelegramConflictError` and the second exits immediately.

## Architecture

### Request flow

Every Telegram update passes through `AccessMiddleware` (`bot/middlewares/access.py`) before any handler:

1. `sync_user()` upserts the Telegram user (username changes are tracked automatically).
2. `store` and `user` objects are injected into handler kwargs.
3. Banned users are blocked except for `/help`, `/privacy`, `/id`, and `/delete`.
4. `react:` callbacks are rate-limited (1-second cooldown, stored in FSM state).
5. `RuleError` is caught here and shown to the user as a plain message; `TelegramForbiddenError` hides the offending profile.

`Store` (`bot/services/store.py`) is the single service/persistence class. Every public method opens its own `AsyncSession`; there is no shared session. Handlers stay thin — all business logic and DB writes go in `Store`.

### Router registration order (in `create_dispatcher`)

`start → admin → profile → discovery → matches → moderation → registration → fallback`

Order matters: `admin` must precede other command routers so `/ban`/`/unban` are not shadowed.

### FSM

FSM state is kept in aiogram's in-memory `MemoryStorage`. On bot restart, incomplete forms, preview state, and the 1-second reaction cooldown are lost; saved profiles are unaffected.

FSM groups (in `bot/states.py`):
- `Registration` — 10-step flow: adult → consent → username → name → age → gender → seeking → location → bio → photo → preview
- `Edit` — single-value field edits (`edit:<field>` callbacks)
- `Search` — age-range update
- `Complaint` — report flow: reason → optional comment → confirm

### Matching algorithm (`Store._candidates`)

Candidates are filtered by reciprocal gender/seeking compatibility and reciprocal age-range compatibility. Both the actor and the candidate must be active, unblocked, and unreacted. When both have coordinates, results are sorted by Haversine distance (nearest first) and `own_city_only` is respected on both sides. No maximum radius — if no nearby profiles exist, farther ones are shown.

### Concurrency safety

`Store.decide()` acquires a PostgreSQL advisory lock with `pg_advisory_xact_lock(user_low_id, user_high_id)` inside the reaction transaction. Combined with `UNIQUE ON CONFLICT`, this prevents duplicate reactions and double-match creation under concurrent `react:` callbacks. Match notifications are sent **after** the transaction commits, outside any session.

### Domain exception pattern

`RuleError(ValueError)` (from `bot/services/validation.py`) is the only expected exception that travels up to `AccessMiddleware`. Handlers raise it for user-facing rejections (banned user tries to like, invalid field value, unauthorized admin action, etc.). Everything else is a real error and is logged.

### UI text and backward compatibility

All Russian UI strings are in `bot/texts.py`. `MENU_LABELS` is the canonical tuple (6 items). `PREVIOUS_MENU_LABELS` (older Russian labels) and `LEGACY_MENU_LABELS` (Uzbek labels) are combined into `MENU_LABEL_ALIASES` frozensets. Menu message handlers match on the union of all aliases so users with old reply keyboards continue working after a UI-language change.

### Discovery message reuse

`bot/handlers/discovery.py` tracks the current profile message in FSM state (`MESSAGE_ID_KEY`, `PHOTO_ID_KEY`). Subsequent profiles reuse the same Telegram message via `edit_message_caption` (same photo) or `edit_message_media` (different photo), rather than sending a new message each time. `"message to edit not found"` causes a fallback to a fresh `answer_photo`.

### Profile deletion vs. user retention

`Store.delete_profile()` removes the profile row, all reactions, and all matches, and clears `username` from the User row. The User row itself is kept (with `telegram_id`, internal `id`, `is_banned`, `created_at`) so moderation records (Block, Report) retain their foreign-key targets.

### Configuration

`Settings` (Pydantic BaseSettings, `bot/config.py`) reads from `.env`. `normalize_database_url()` converts bare `postgres://` and `postgresql://` URL schemes to `postgresql+asyncpg://` (Railway compatibility). Only PostgreSQL is accepted; SQLite raises `ValueError`.

`ADMIN_IDS` is a list of Telegram IDs (integers). Admin authorization is rechecked on every admin command and callback, not cached.
