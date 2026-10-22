# Sanya — Personal Assistant

Telegram-first personal assistant with a web dashboard. Four skills are live: Expense Tracking, Reminders, Todo, and Tech / AI News.

## What this project includes

- Docker Compose app: Postgres, FastAPI API + Telegram bot, React dashboard
- Shared LLM providers: Groq, Gemini, OpenRouter, and an optional OpenAI-compatible endpoint
- Skill registry: each skill has its own parser, then optional save or execute
- Supabase-ready Postgres schema (`supabase/migrations`)
- Natural-language capture through Telegram, with the same actions on the dashboard
- Reminder and due-todo alerts sent back to Telegram

## Prerequisites

- Docker and Docker Compose
- A [Supabase](https://supabase.com) project (Postgres), or the local Docker Postgres included for a first run
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- At least one LLM key: `GROQ_API_KEY`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY`, or `OPENAI_API_KEY`. Leave them empty to use keyword and regex fallbacks.

## Installation and setup

1. Copy the env file: `cp .env.example .env`
2. Set `DATABASE_URL`.
   - Supabase session pooler (IPv4, works in Docker): `postgresql://postgres.YOUR_PROJECT_REF:YOUR_PASSWORD@aws-0-ap-south-1.pooler.supabase.com:5432/postgres?sslmode=require`. The user must be `postgres.PROJECT_REF`. Do not use the transaction pooler (`6543`).
   - Direct host (`db.YOUR_PROJECT_REF.supabase.co`) is often IPv6-only.
   - Local Docker Postgres: `postgresql://expense:expense@db:5432/expenses`. Compose already starts that container.
   - If the password contains `@`, `#`, or `%`, URL-encode it. Tables are created on backend startup. You can also run `supabase/migrations/*.sql` in the Supabase SQL editor.
3. Set `TELEGRAM_BOT_TOKEN`. Set `ALLOWED_TELEGRAM_USER_IDS` to your numeric Telegram id (from `@userinfobot`) or username. Leave it empty to allow every user.
4. Set `DEFAULT_LLM_PROVIDER=gemini` (or `groq` / `openrouter` / `openai` / `auto`) and the matching API key. No spaces after `=`. That provider is tried first. If its key is empty or the call fails, the free-first order below is used.
5. Optional: `APP_TIMEZONE` (default `Asia/Kolkata`), `DEFAULT_CURRENCY` (default `INR`), and `DEFAULT_SKILL` (default `expense_tracking`).
6. Start: `docker compose up --build`
7. Open the dashboard at `http://localhost:3001` and the API at `http://localhost:8000/api/health`. `"llm": true` plus `"llm_provider": "gemini"` means that provider is the one that will be tried first.

## Skills

Sanya picks a skill, then runs that skill's parser. Pin one with `/use`, a command such as `/expenses`, or a prefix (`expenses: tiffin 80`). If routing is unsure, `DEFAULT_SKILL` is used.

### Expense Tracking

Log spends and see daily, weekly, and monthly totals by category and place.

Examples:

- `tiffin 80`
- `petrol 500 at Indian Oil`
- `oct 1 tiffin 135`
- `eating outside 250 at Cafe Coffee Day`

Commands: `/expenses` `/today` `/week` `/month` `/list` `/categories` `/addcategory` `/undo`

The dashboard has summary, history, and add-expense views, plus category breakdowns.

### Reminders

Natural-language reminders with a due time. The bot sends a Telegram alert before the due time and again when it is due.

Examples:

- `remind me to call dentist tomorrow 10am`
- `remind buy milk in 2 hours`
- `list`
- `delete dentist`

Command: `/reminders`

The dashboard can add, edit, and delete reminders.

### Todo

Capture tasks from chat, mark them done, and delete them. Due tasks can also trigger a Telegram alert.

Examples:

- `todo submit invoice tomorrow`
- `add todo buy groceries`
- `done invoice`
- `delete groceries`
- `list` or `completed`

Command: `/todo`

The dashboard lists open and completed tasks and lets you set a due date.

### Tech / AI News

Headlines for AI, tech, and top stories, pulled from public RSS feeds (Hacker News and The Verge) and stored as daily digests.

Examples:

- `ai news today`
- `tech headlines`
- `top news`

Command: `/news`

The dashboard switches between AI, tech, top, and locally saved headlines.

## Telegram bot

`/start`, `/help`, and `/menu` open the home keyboard and action buttons.

| Button | Actions |
| --- | --- |
| Expenses | Add, summary, history |
| Reminders | Add, list, delete |
| Todo | Add, list, completed, delete |
| News | AI, tech, top |

Other commands: `/skills` (alias `/tools`), `/use expense_tracking` (aliases: `expenses`, `reminder`, `todo`, `tasks`).

## LLM providers

Shared client in `backend/app/llm/`. Skills never talk to a vendor SDK directly.

| Order | Provider | Free? | Env key | Default model |
| --- | --- | --- | --- | --- |
| 1 | Gemini | Yes, best free quota and quality | `GEMINI_API_KEY` | `gemini-3.8-flash` |
| 2 | Groq | Yes, fastest free tier | `GROQ_API_KEY` | `openai/gpt-oss-120b` |
| 3 | OpenRouter | Yes, about 50 free requests a day | `OPENROUTER_API_KEY` | `openrouter/free` |
| 4 | OpenAI | Paid | `OPENAI_API_KEY` | `gpt-4o-mini` |

`DEFAULT_LLM_PROVIDER` is tried first. The default value is `gemini`. If that key is empty or the call fails, the table order follows. `DEFAULT_LLM_PROVIDER=auto` skips the pin and uses the table order directly. Groq retired `llama-3.3-70b-versatile` on its free plan, so the Groq default is `openai/gpt-oss-120b`. Each skill has its own prompt and JSON shape in `backend/app/skills/<skill>/parser.py`. If no LLM key is set, that parser's fallback still runs.

## Folder structure

```
backend/app/
  api/                 Shared HTTP mounts (/api/skills, /api/health)
  bot/                 Telegram dispatcher, menus, and callbacks
  llm/                 complete_json + Groq, Gemini, OpenRouter, OpenAI
  models/              SQLAlchemy base and model imports
  time.py              Shared timezone helpers (today / week / month)
  when.py              Natural-language due-time parser (in N hours, tomorrow 10am…)
  origin.py            Source tagging helpers (web vs telegram)
  skills/
    expense_tracking/  Parser, models, routes, Telegram commands
    reminders/         Parser, models, routes, due-time alerts
    todo/              Parser, models, routes, done / delete
    news/              Parser, RSS digests, routes
frontend/src/
  components/          Shared UI pieces (charts, tables, forms)
  skills/              Dashboard screen per skill
supabase/migrations/   Postgres schema (also used by Docker Postgres on first run)
```

To add a skill: add `backend/app/skills/<name>/` with `parser.py` and `skill.py`, register it in `backend/app/skills/registry.py`, and add a dashboard screen under `frontend/src/skills/`.

## Main API

- `GET /api/health`
- `GET /api/skills`
- `POST /api/skills/parse` `{ "text": "...", "skill": "expense_tracking" }`
- `POST /api/skills/handle` same body; parses and saves or runs the skill
- `GET /api/expenses?period=today|week|month`
- `POST /api/expenses`
- `DELETE /api/expenses/{id}`
- `GET /api/summaries?period=today|week|month`
- `GET /api/categories`
- `POST /api/categories`
- `GET /api/reminders?include_done=false`
- `POST /api/reminders`
- `PATCH /api/reminders/{id}`
- `DELETE /api/reminders/{id}`
- `GET /api/todos?status=open|done|all`
- `POST /api/todos`
- `PATCH /api/todos/{id}`
- `DELETE /api/todos/{id}`
- `GET /api/news?topic=ai|tech|top&day=YYYY-MM-DD&refresh=false`
- `GET /api/news/days?topic=ai|tech|top`
