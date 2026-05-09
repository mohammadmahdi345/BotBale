# BotBale

BotBale is a production-oriented Python scaffold for an AI-powered Persian immigration
consultation bot on Bale Messenger. It uses FastAPI webhooks, PostgreSQL persistence,
OTP-based phone authentication, OpenAI-compatible AI consultation, interactive Bale keyboards,
subscription-aware usage limits, and modular services that are easy to extend in VS Code.

## Features

- Python 3.11+ FastAPI application for Bale webhook updates.
- Persian-language conversation flow with reply-keyboard menus.
- Immigration consultation workflow:
  - انتخاب بهترین کشور بر اساس روش مهاجرت
  - مهاجرت کاری
  - مهاجرت تحصیلی
  - مهاجرت سرمایه گذاری
  - ویزای استارتاپ
  - اقامت دائم
- Specialized follow-up questions for education, experience, language, budget,
  destination preferences, age, family status, and route-specific details.
- OpenAI API integration for natural Persian recommendations.
- Topic guard that refuses unrelated questions and redirects users to immigration topics.
- Dynamic phone-number authentication with OTP SMS verification.
- Secure user storage:
  - encrypted phone number
  - HMAC phone hash for duplicate prevention
  - full name
  - registration date
  - subscription type
- Persistent session state, consultation history, usage counters, and conversation logs.
- Daily usage limits:
  - Free: 5 AI questions/consultations per day
  - Premium: 30 AI questions/consultations per day
  - reset is automatic because counters are stored per user and date.
- Alembic migrations and Docker Compose PostgreSQL for local development.
- VS Code launch/test settings.

## Architecture

```text
app/
  api/            FastAPI routes for health checks and Bale webhooks
  bale/           Bale HTTP client and keyboard definitions
  config/         Environment-driven settings
  core/           Logging and security helpers
  db/             SQLAlchemy async database setup
  models/         PostgreSQL persistence models
  repositories/   Data-access helpers
  schemas/        Pydantic request/response schemas
  services/       Auth, SMS, AI, usage limits, topic guard, bot state machine
  workflows/      Immigration consultation question flows
tests/            Focused unit tests
alembic/          Database migrations
```

## Local setup in VS Code

1. Create a virtual environment and install dependencies:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   ```

2. Start PostgreSQL:

   ```bash
   docker compose up -d postgres
   ```

3. Create `.env`:

   ```bash
   cp .env.example .env
   python3 - <<'PY'
   from cryptography.fernet import Fernet
   print(Fernet.generate_key().decode())
   PY
   ```

   Put the generated value in `PHONE_ENCRYPTION_KEY`, then configure:

   - `BALE_BOT_TOKEN`
   - `WEBHOOK_SECRET`
   - `OPENAI_API_KEY`
   - `OTP_SECRET`
   - optional SMS provider values

4. Run migrations:

   ```bash
   alembic upgrade head
   ```

5. Run the application:

   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. Configure Bale webhook to:

   ```text
   https://your-domain.example/webhooks/bale/<WEBHOOK_SECRET>
   ```

   If you proxy requests yourself, you may also pass the same secret in the
   `X-Webhook-Secret` header.

## SMS provider

`SMSService` supports a generic JSON POST provider:

```json
{
  "to": "+989123456789",
  "sender": "BotBale",
  "message": "کد ورود شما ..."
}
```

Leave `SMS_PROVIDER_URL` empty in local development to log OTPs instead of sending SMS.
For production, configure your provider URL and API key.

## Bale API

`BaleClient` posts messages to:

```text
<BALE_API_BASE_URL>/bot<BALE_BOT_TOKEN>/sendMessage
```

The default base URL is `https://tapi.bale.ai`. If Bale changes endpoints or your account
uses a dedicated gateway, update `BALE_API_BASE_URL`.

## Subscription management

Users are stored with `subscription_type = free` by default. Upgrade a user to premium through
an admin tool, payment webhook, or direct database operation until a payment module is added.
Daily counters are stored by `(user_id, usage_date)`, so a new row is automatically created
on the next UTC day.

## Security notes

- Keep `.env` out of Git.
- Use strong random values for `WEBHOOK_SECRET` and `OTP_SECRET`.
- Generate `PHONE_ENCRYPTION_KEY` with `cryptography.fernet.Fernet.generate_key()`.
- OTP codes are HMAC-hashed and expire after `OTP_TTL_SECONDS`.
- Phone numbers are encrypted at rest and deduplicated with a keyed HMAC hash.
- The webhook route rejects requests with an invalid secret.

## Testing and linting

```bash
pytest
ruff check .
```

## Extending the bot

- Add new consultation flows in `app/workflows/immigration.py`.
- Add payment/subscription callbacks in `app/api/`.
- Replace the generic SMS integration in `app/services/sms.py` with your provider SDK.
- Add richer immigration-topic classification by expanding `TopicGuard` or using a small AI
  classification prompt before answering.
