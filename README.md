# Customer Service AI Agent (CSAA) Application — Event-Driven Agentic Voice & Messaging Platform

Customer Service AI Agent (CSAA) Application is a multi-tenant platform for building, deploying, and monitoring conversational AI agents that answer real phone calls, WhatsApp threads, and SMS conversations on behalf of an organization. A Django ASGI backend brokers every turn of a conversation between Twilio (telephony), OpenAI (reasoning), and ElevenLabs (voice synthesis), while a Next.js dashboard streams live conversation state over WebSockets so a human operator can watch, take over, or hand a conversation back to the agent mid-flight.

**Repository layout**

| Path                                              | Contents                                                                                                     |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| [backend/](backend/)                               | Django 5.0 ASGI project (`core`), six domain apps (`apps/*`), and the integration layer (`services/*`) |
| [frontend/](frontend/)                             | Next.js 15 App Router dashboard (React 19, Tailwind v4, shadcn/ui)                                           |
| [README.progressplan.md/](README.progressplan.md/) | Phase plans, testing notes, and the local run checklist                                                      |

---

## 1. Tech Stack Overview

### Backend

| Concern                           | Technology                                                                                                                                                                                                                                                                                        | Where it lives                                                                                                                                     |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Web framework**           | Django`5.0` with **django-ninja `1.4.3`** for the typed REST surface (Pydantic `2.11.7` schemas, auto-generated OpenAPI at `/api/docs`)                                                                                                                                             | [core/api.py](backend/core/api.py), [core/urls.py](backend/core/urls.py)                                                                             |
| **Async runtime**           | **ASGI** via `ASGI_APPLICATION = "core.asgi.application"`, served by **Daphne `4.2.1`** (Twisted `25.5.0` / autobahn `24.4.2`); `asgiref 3.9.1` bridges sync ORM calls                                                                                                      | [core/asgi.py](backend/core/asgi.py), [core/settings/base.py:125](backend/core/settings/base.py#L125)                                                |
| **Real-time transport**     | **Django Channels `4.3.1`** — `ProtocolTypeRouter` splits HTTP from WebSocket, guarded by `AllowedHostsOriginValidator` + a custom `JWTAuthMiddleware`                                                                                                                             | [apps/conversations/routing.py](backend/apps/conversations/routing.py), [apps/conversations/middleware.py](backend/apps/conversations/middleware.py) |
| **Channel layer / pub-sub** | **`channels_redis 4.3.0`** `RedisChannelLayer` (capacity 1500, expiry 10s) — fans conversation events out to `org_<uuid>` groups                                                                                                                                                     | [core/settings/base.py:252-260](backend/core/settings/base.py#L252-L260)                                                                            |
| **Task queue**              | **Celery `5.5.3`** workers + **`django-celery-beat 2.8.1`** scheduler + **Flower `2.0.1`** monitoring; results persisted to the DB via `django_celery_results 2.6.0`                                                                                                    | [core/celery.py](backend/core/celery.py), [apps/analytics/tasks.py](backend/apps/analytics/tasks.py)                                                 |
| **Message broker**          | **Redis `6.4.0` (client)** — serves as *both* the Celery broker/result transport and the Channels backplane. `kombu 5.5.4` / `amqp 5.3.1` ship as Celery dependencies, so switching the broker to **RabbitMQ** is a one-line `CELERY_BROKER_URL` change with no code edits | [core/settings/base.py:295-296](backend/core/settings/base.py#L295-L296)                                                                            |
| **Database & ORM**          | Django ORM against**PostgreSQL** (`psycopg2-binary 2.9.10`); `development.py` falls back to SQLite, `production.py` reads `DATABASE_URL` through `dj-database-url 3.0.1`                                                                                                          | [core/settings/base.py:133-141](backend/core/settings/base.py#L133-L141)                                                                            |
| **Auth**                    | `djangorestframework-simplejwt 5.5.1` — HS256, 2 h access / 7 day refresh with rotation; the same `AccessToken` validates the WebSocket handshake                                                                                                                                            | [core/settings/base.py:270-291](backend/core/settings/base.py#L270-L291)                                                                            |
| **Supporting**              | `django-cors-headers 4.7.0`, `whitenoise 6.9.0` (compressed manifest static storage), `PyPDF2 3.0.1` (knowledge-base ingestion), `boto3 1.40.5` (optional S3 audio offload), `phonenumbers 9.0.11`, `prometheus_client 0.22.1`                                                        | [requirements.txt](backend/requirements.txt)                                                                                                        |
| **Runtime**                 | Python 3.10 (`python:3.10-slim` base image)                                                                                                                                                                                                                                                     | [backend/Dockerfile](backend/Dockerfile)                                                                                                            |

### Frontend

| Concern                      | Technology                                                                                                                                                                                                             |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Framework**          | **Next.js `15.4.6`** (App Router, route groups `(auth)` / `(dashboard)`) on **React `19.1.0`** + **TypeScript 5**                                                                            |
| **Styling & UI**       | **Tailwind CSS v4** (`@tailwindcss/postcss`), **shadcn/ui** on Radix primitives (dialog, select, tabs, popover, toast, tooltip…), `lucide-react` icons, `next-themes` dark mode, `tw-animate-css` |
| **Server state**       | **TanStack Query `5.84.2`** (60 s stale time, no retry on 401) — [src/app/providers.tsx](frontend/src/app/providers.tsx)                                                                                       |
| **Client state**       | **Zustand `5.0.7`** stores for auth and conversations — [src/lib/stores/](frontend/src/lib/stores/)                                                                                                            |
| **HTTP**               | **Axios `1.11.0`** with a bearer-token request interceptor and a single-flight refresh-token retry queue — [src/lib/api/client.ts](frontend/src/lib/api/client.ts)                                             |
| **Realtime**           | Native`WebSocket` wrapper with typed event emitter and exponential-backoff reconnect (5 attempts) — [src/lib/websocket.ts](frontend/src/lib/websocket.ts)                                                            |
| **Forms & validation** | `react-hook-form 7.62` + `zod 4.0.17` via `@hookform/resolvers`                                                                                                                                                  |
| **Charts**             | **Recharts `3.1.2`** for the analytics surfaces                                                                                                                                                                |
| **Deployment**         | **Railway** via Dockerfile builder (`healthcheckPath = "/"`) — [frontend/railway.toml](frontend/railway.toml). Vercel-compatible; `next.config.ts` carries no custom build config                            |

### Third-Party APIs & Services

| Role                                | Service                                                                                                                                                                                                                                                                                                                                              | Implementation                                                          |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| **Telephony & call control**  | **Twilio Voice API + Programmable Messaging** (`twilio 9.7.0`, `django-twilio 0.14.3.3`) — inbound voice/SMS/WhatsApp webhooks, TwiML generation (`VoiceResponse`, `Gather`, `Play`), `RequestValidator` signature checks, and programmatic phone-number provisioning/release                                                     | [services/twilio_service.py](backend/services/twilio_service.py)         |
| **Speech-to-Text**            | **Twilio `<Gather input="speech">`** — Twilio performs ASR and posts the transcript back as the `SpeechResult` form field. *No separate STT vendor is wired up.*                                                                                                                                                                        | [apps/webhooks/api.py:256-272](backend/apps/webhooks/api.py#L256-L272)   |
| **Text-to-Speech**            | **ElevenLabs `2.10.0` SDK** — `AsyncElevenLabs.text_to_speech.convert()` on model **`eleven_flash_v2_5`**, default voice `21m00Tcm4TlvDq8ikWAM` (Rachel), `VoiceSettings(stability=0.5, similarity_boost=0.5)`. A second synchronous client powers in-dashboard voice previews and a 24 h `ElevenLabsVoice` catalogue cache | [services/elevenlabs_service.py](backend/services/elevenlabs_service.py) |
| **Intelligence / brain**      | **OpenAI `1.99.3`** (`AsyncOpenAI`) — per-agent model selection between **`gpt-4`** (default) and **`gpt-3.5-turbo`**, with `gpt-3.5-turbo` used for sentiment scoring and intent extraction. Every completion's `prompt_tokens`/`completion_tokens` is written to `UsageLog` for billing                         | [services/ai_service.py](backend/services/ai_service.py)                 |
| **Object storage (optional)** | AWS S3 via`boto3` — env keys are provisioned; audio currently persists to `MEDIA_ROOT/audio` and is deleted after playback                                                                                                                                                                                                                      | [.env.example](backend/.env.example)                                     |

> **Dependency note:** `elevenlabs==2.10.0` is installed in the working virtualenv and imported by `services/elevenlabs_service.py`, but is **absent from [backend/requirements.txt](backend/requirements.txt)**. Add it before building a clean image, or the container will fail at import time.

---

## 2. End-to-End System Architecture & Call Flow

Luron's voice loop is **turn-based rather than bidirectionally streamed**: Twilio handles ASR and posts each finished utterance to a Django webhook; the backend answers with TwiML that plays an ElevenLabs-synthesised MP3 and immediately re-opens a `<Gather>` for the next turn. Every non-critical side effect (message persistence broadcasts, status callbacks, metric rollups) is pushed off the request path so the caller never waits on it.

### Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Customer
    participant Twilio as Twilio Voice API
    participant Server as Django Backend (ASGI / Daphne)
    participant Broker as Redis (Channels layer + Celery broker)
    participant ElevenLabs as ElevenLabs API
    participant LLM as OpenAI (AIService)
    participant Dashboard as Next.js Dashboard

    Customer->>Twilio: Inbound phone call
    Twilio->>Server: POST /api/webhooks/twilio/voice
    Server->>Server: Resolve Agent by voice_number (voice_enabled, is_active)
    Server->>ElevenLabs: text_to_speech(welcome_message, agent.voice_id)
    ElevenLabs-->>Server: MP3 audio bytes -> saved to /media/audio
    Server-->>Twilio: TwiML <Play>{audio_url}</Play> + <Gather input="speech">
    Twilio-->>Customer: Plays synthesised greeting
    Server->>Server: asyncio.create_task(create_voice_conversation)

    Customer->>Twilio: Speaks
    Twilio->>Twilio: Speech recognition (Gather)
    Twilio->>Server: POST /twilio/voice/process/{agent_id} (SpeechResult)
    Server->>Server: MessageProcessor.process_voice_speech()
    Server->>LLM: system prompt + knowledge base + last 10 turns + utterance
    LLM-->>Server: Agent response text (+ token usage)
    Server->>ElevenLabs: text_to_speech(response, eleven_flash_v2_5)
    ElevenLabs-->>Server: Streamed audio chunks -> audio_url
    Server-->>Twilio: TwiML <Play>{audio_url}</Play> + <Gather>
    Twilio-->>Customer: Real-time synthesised voice response

    Server->>Broker: channel_layer.group_send("org_<uuid>", conversation_update)
    Broker-->>Dashboard: WebSocket push (ws/conversations/)
    Server->>Broker: Celery beat -> aggregate_metrics / aggregate_daily_metrics
    Twilio->>Server: POST /api/webhooks/twilio/status (delivery callbacks)
```

### Step-by-Step Call Lifecycle

1. **Inbound call ingestion.** The customer dials a Twilio number. Twilio POSTs `From`, `To`, and `CallSid` to `POST /api/webhooks/twilio/voice`, handled by the `async def voice_incoming_webhook` coroutine in [apps/webhooks/api.py](backend/apps/webhooks/api.py).
2. **Asynchronous handshake (ASGI).** Daphne dispatches the webhook onto the event loop. The backend resolves the owning agent with `Agent.objects.select_related('organization').get(voice_number=to_number, voice_enabled=True, is_active=True)` wrapped in `asyncio.to_thread`, so the blocking ORM call never stalls the loop. An unmatched number gets a graceful "not in service" TwiML instead of an error.
3. **Greeting synthesis.** The agent's `welcome_message` is sent to `ElevenLabsService.text_to_speech()`. The async SDK streams chunks, they are joined into a single MP3, written to `MEDIA_ROOT/audio/` off-thread, and exposed at `{MEDIA_PUBLIC_DOMAIN}/media/audio/<file>.mp3` (an ngrok URL in local development). If ElevenLabs fails, the handler transparently falls back to Twilio's built-in `<Say>` TTS.
4. **Session creation, off the hot path.** `asyncio.create_task(create_voice_conversation_async(...))` fires and forgets the `Conversation` row creation, so the TwiML response returns to Twilio immediately rather than waiting on a database round trip.
5. **Speech-to-text.** The returned `<Gather input="speech" speechTimeout="auto">` instructs Twilio to transcribe the caller's next utterance. Twilio POSTs the transcript to `/api/webhooks/twilio/voice/process/{agent_id}` as `SpeechResult`. Empty results trigger a "could you please repeat?" re-prompt rather than dropping the call.
6. **Agentic LLM execution.** `MessageProcessor.process_incoming_message(channel='voice', ...)` in [services/message_processor.py](backend/services/message_processor.py) persists the customer turn, loads the last 10 messages as history, then calls `AIService.generate_response()`. The system prompt is assembled from the agent's `system_prompt`, `personality_traits`, organization name, customer name, language, and up to five processed `KnowledgeDocument` records. Generation runs at the agent's configured `temperature`/`max_tokens` on its selected model, and token usage is written to `UsageLog` for billing.
7. **Human-in-the-loop short circuit.** If an operator has taken the conversation over (`status == 'handed_off'`), the LLM step is skipped entirely — the inbound turn is stored and broadcast to the dashboard so the human replies directly. `POST /conversations/{id}/handoff` and `/handoff_back_to_ai_agent` flip that state.
8. **Speech synthesis & telephony delivery.** The response text goes back through ElevenLabs' `eleven_flash_v2_5` model (chosen for latency and cost), and `TwilioService.generate_play_twiml()` emits `<Play>{audio_url}</Play>` followed by a fresh `<Gather>` — playing the answer and re-arming the microphone in a single TwiML document. Once played, the local MP3 is deleted by `_delete_audio_file_local()` to bound disk growth.
9. **Event fan-out over the Channels backplane.** `_broadcast_conversation_update()` publishes to the `org_<organization_id>` group through the `channels_redis` layer. Connected `ConversationConsumer` sockets — authenticated by JWT at handshake and joined to both `org_<uuid>` and `user_<uuid>` groups — receive `conversation_update`, `new_conversation`, and `conversation_status_changed` frames. `AgentConsumer` (`ws/agent/<agent_id>/`) and `OrganizationConsumer` (`ws/organization/`) carry agent-status and usage events.
10. **Metrics, billing, and status reconciliation.** Sentiment (`gpt-3.5-turbo`), response-time deltas, and per-conversation counters are updated inline; Twilio delivery receipts arrive at `/api/webhooks/twilio/status` and are applied in a background task that always returns `200` so Twilio never retries. Celery beat then rolls raw conversations into `HourlyMetrics` hourly (`aggregate_metrics`), into `DailyMetrics` with cost attribution nightly at 00:05 (`aggregate_daily_metrics`), and prunes old rows weekly (`cleanup_old_metrics`).

### Channel Parity

The same `MessageProcessor` pipeline serves all three channels; only ingress and egress differ:

| Channel            | Webhook                                                              | Response path                                                        |
| ------------------ | -------------------------------------------------------------------- | -------------------------------------------------------------------- |
| **Voice**    | `POST /api/webhooks/twilio/voice` → `/voice/process/{agent_id}` | ElevenLabs MP3 → TwiML`<Play>` + `<Gather>`                     |
| **WhatsApp** | `POST /api/webhooks/twilio/whatsapp`                               | `client.messages.create` (`whatsapp:` prefixed), media supported |
| **SMS**      | `POST /api/webhooks/twilio/sms`                                    | `client.messages.create`, truncated at 1600 chars                  |

---

## 3. Key Backend Architecture Features

**Non-blocking async webhook handlers.** Every Twilio webhook is an `async def` coroutine served by Daphne. Twilio's ~10 s webhook budget is respected by acknowledging first and working second: `asyncio.create_task()` detaches message processing for WhatsApp and SMS, conversation creation for voice, and status reconciliation for delivery receipts. Blocking Django ORM calls are consistently wrapped in `asyncio.to_thread()` / `sync_to_async(thread_sensitive=True)` / `database_sync_to_async`, so no synchronous query is ever awaited on the event loop.

**Redis as a dual-purpose event bus.** One Redis instance backs two independent planes: `channels_redis.core.RedisChannelLayer` for WebSocket group fan-out (`org_<uuid>`, `user_<uuid>`, `agent_<uuid>`), and the Celery broker/result transport for deferred work. The publisher (`MessageProcessor`) never knows which dashboards are connected — it publishes to an organization group and the layer handles delivery, which keeps the voice loop fully decoupled from the UI. Because `kombu`/`amqp` are already resolved as Celery dependencies, repointing `CELERY_BROKER_URL` at a RabbitMQ instance requires no application changes.

**Task decoupling and scheduled aggregation.** Analytics never run on the request path. `apps/analytics/tasks.py` defines idempotent, retry-bounded (`bind=True, max_retries=3`) Celery tasks that walk organizations independently, and `core/celery.py` schedules them with `crontab` triggers. `CELERY_TASK_TIME_LIMIT` (30 min hard / 25 min soft) bounds runaway jobs, and `django_celery_results` persists outcomes to Postgres for post-hoc debugging.

**JWT-authenticated WebSockets.** `JWTAuthMiddleware` extracts the `token` query parameter during the ASGI handshake, validates it with SimpleJWT's `AccessToken`, and resolves the `User` (with `select_related('organization')`) into the connection scope before the consumer runs. `BaseConsumer.connect()` then rejects with distinct close codes — `4001` unauthenticated, `4002` no organization, `4003` internal error — which the frontend's reconnect logic can act on. Origin is independently enforced by `AllowedHostsOriginValidator`.

**Multi-tenant isolation by construction.** `Organization` is the tenant root; `User`, `Agent`, `Conversation`, `UsageLog`, `HourlyMetrics`, and `DailyMetrics` all descend from it, and every API handler filters on `request.auth.organization`. Group names are derived from the organization UUID, so realtime events are scoped to a tenant at the transport layer, not just at query time.

**Usage metering wired into the integration layer.** Cost accounting is not a reporting afterthought — `UsageLog` rows are written at the point of spend: OpenAI token counts in `AIService._log_token_usage()`, TTS character counts (`$0.00018/char`) in `ElevenLabsService._log_usage()`, and per-message SMS cost (`$0.0075`) in `TwilioService.send_sms()`. The billing API aggregates those rows against `Organization.monthly_message_limit` and `monthly_voice_minutes_limit`.

**Graceful degradation at every external boundary.** ElevenLabs failure falls back to Twilio TTS; a missing ElevenLabs key disables the service rather than crashing at import; the voice catalogue serves an expired DB cache (and then a hardcoded voice list) when the API is unreachable; LLM errors return a spoken apology instead of a 500; and status callbacks always return `200` to suppress Twilio retry storms.

**Typed, self-documenting API surface.** django-ninja composes six routers under a single `NinjaAPI` at `/api/` — `auth`, `agents`, `conversations`, `analytics`, `billing`, `webhooks` — with Pydantic request/response schemas and interactive OpenAPI docs at `/api/docs`. Webhook routes are explicitly declared `auth=None` and CSRF-exempt, keeping the unauthenticated attack surface small and visible.

### Domain Apps

| App                                             | Responsibility                                                                                                       | Key endpoints                                                                                          |
| ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| [apps/accounts](backend/apps/accounts)           | `Organization` + custom UUID `User` (roles: owner/admin/agent), JWT issuance                                     | `/api/auth/login`, `/register`, `/refresh`, `/me`, `/change-password`                        |
| [apps/agents](backend/apps/agents)               | Agent config (prompt, persona, model, voice, channels, business hours), templates, PDF knowledge base, voice preview | `/api/agents/`, `/{id}/knowledge`, `/voices`, `/{id}/preview-voice`, `/{id}/test-chat`       |
| [apps/conversations](backend/apps/conversations) | `Conversation`/`Message` models, WebSocket consumers, search & export, human handoff                             | `/api/conversations/`, `/search`, `/{id}/handoff`, `/{id}/end`, `/export`                    |
| [apps/webhooks](backend/apps/webhooks)           | Twilio ingress for voice, SMS, WhatsApp, and status callbacks                                                        | `/api/webhooks/twilio/{voice,sms,whatsapp,status}`                                                   |
| [apps/analytics](backend/apps/analytics)         | `HourlyMetrics`/`DailyMetrics`, Celery rollups, trends, peak hours, CSV/JSON export                              | `/api/analytics/overview`, `/conversation-flow`, `/customer-insights`, `/time-series/{metric}` |
| [apps/billing](backend/apps/billing)             | `UsageLog` ledger, quota tracking, subscription tiers                                                              | `/api/billing/usage`, `/usage/current`, `/subscription`                                          |

---

## 4. Local Development Setup & Prerequisites

### Prerequisites

- **Python 3.10** (the Docker image pins `python:3.10-slim`)
- **Node.js 18+** and npm
- **PostgreSQL 14+** listening on `5432` (or use the SQLite fallback via `core.settings.development`)
- **Redis 6+** on `6379` — required for both Channels and Celery
- **ngrok** (or any HTTPS tunnel) — Twilio must reach your webhooks over a public HTTPS URL
- Accounts for **Twilio**, **OpenAI**, and **ElevenLabs**

### Environment Variables

Copy [backend/.env.example](backend/.env.example) to `backend/.env`:

```bash
# Django
SECRET_KEY=your-django-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,.ngrok-free.app

# Database — PostgreSQL is the default in core/settings/base.py
POSTGRESQL_DB_NAME=luron_db
POSTGRESQL_USER=postgres
POSTGRESSQL_PASSWORD=your_db_password     # note: spelling matches settings/base.py
POSTGRESQL_HOST=localhost
POSTGRESQL_PORT=5432
DATABASE_URL=postgresql://user:pass@localhost:5432/luron_db  # used by production.py

# Redis — Channels layer, Celery broker, and Celery results
REDIS_URL=redis://localhost:6379
REDIS_HOST=127.0.0.1
REDIS_PORT=6379

# LLM
OPENAI_API_KEY=sk-your-openai-api-key-here

# Telephony
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_WHATSAPP_NUMBER=+1234567890
TWILIO_SMS_NUMBER=+1234567890
TWILIO_VOICE_NUMBER=+1234567890

# Voice synthesis
ELEVENLABS_API_KEY=sk_your-elevenlabs-api-key-here

# URLs — WEBHOOK_BASE_URL must be your public HTTPS tunnel, since Twilio
# fetches the generated MP3 from {MEDIA_PUBLIC_DOMAIN}/media/audio/...
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
WEBHOOK_BASE_URL=https://your-subdomain.ngrok-free.app

# Optional — S3 offload for generated audio
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=
AWS_S3_REGION_NAME=us-east-1
```

Copy [frontend/.env.example](frontend/.env.example) to `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_APP_NAME=Customer Service AI Agent (CSAA) Application
```

> `NEXT_PUBLIC_API_URL` must include the `/api` suffix — [src/lib/config.ts](frontend/src/lib/config.ts) defaults to `http://localhost:8000/api`, while `.env.example` omits it.

### Backend

```bash
cd backend

python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install "elevenlabs==2.10.0"          # imported by services/, missing from requirements.txt

python manage.py migrate
python manage.py createsuperuser          # or: python manage.py create_admin
python manage.py collectstatic --noinput  # WhiteNoise manifest storage
```

You need **five** processes running locally. Each block is its own terminal:

```bash
# 1 — Redis (Channels backplane + Celery broker)
redis-server

# 2 — ASGI server (HTTP + WebSocket). Do NOT use `manage.py runserver` for
#     WebSocket work; Daphne is the configured ASGI server.
daphne -b 127.0.0.1 -p 8000 core.asgi:application

# 3 — Celery worker (analytics aggregation)
celery -A core worker -l info

# 4 — Celery beat (hourly / daily / weekly schedules)
celery -A core beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler

# 5 — Flower dashboard (optional) → http://localhost:5555
celery -A core flower
```

Expose the backend to Twilio and point your numbers at it:

```bash
ngrok http http://localhost:8000
```

Then in the Twilio Console (Manage → Phone Numbers, and the WhatsApp sandbox), set:

| Twilio setting                              | URL                                                     |
| ------------------------------------------- | ------------------------------------------------------- |
| Voice → A call comes in                    | `https://<ngrok>/api/webhooks/twilio/voice` (POST)    |
| Messaging → A message comes in             | `https://<ngrok>/api/webhooks/twilio/sms` (POST)      |
| WhatsApp sandbox → When a message comes in | `https://<ngrok>/api/webhooks/twilio/whatsapp` (POST) |
| Status callback                             | `https://<ngrok>/api/webhooks/twilio/status` (POST)   |

Set `WEBHOOK_BASE_URL` in `backend/.env` to that same ngrok origin and restart Daphne — it is what builds both the `<Gather action=...>` URLs and the publicly fetchable audio URLs.

> **Local signature validation:** `TwilioService.validate_webhook()` compares `request.build_absolute_uri()` against Twilio's signature. Behind ngrok that URL is rewritten, so the check fails. It is already commented out in the WhatsApp handler; the SMS handler still enforces it — comment it out for local testing and re-enable it in production.

Backend surfaces once running:

- API docs (OpenAPI/Swagger): [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
- Django admin: [http://localhost:8000/admin/](http://localhost:8000/admin/)
- WebSockets: `ws://localhost:8000/ws/conversations/?token=<jwt>`, `ws/agent/<agent_id>/`, `ws/organization/`

### Frontend

```bash
cd frontend
npm install
npm run dev          # → http://localhost:3000
```

Other scripts: `npm run build`, `npm run start`, `npm run lint`, `npm run type-check`.

### Docker

```bash
# Backend — bundles redis-server and starts Daphne on :8000 (see entrypoint.sh).
# Celery worker/beat are NOT started by the image; run them separately.
docker build -t luron-backend ./backend
docker run --env-file backend/.env -p 8000:8000 luron-backend

# Frontend
docker build -t luron-frontend ./frontend
docker run -p 3000:3000 luron-frontend
```

Both services carry a [railway.toml](backend/railway.toml) for Railway's Dockerfile builder. Note that the backend's configured `healthcheckPath = "/api/health"` has no matching route in [core/urls.py](backend/core/urls.py) — add one before relying on Railway health checks.

### Verification

```bash
cd backend
python manage.py test                      # Django test runner

python tests/test_websocket_simple.py      # WebSocket handshake + JWT auth
python tests/jwt_token.py                  # mint a token for manual testing
python test_broadcast.py                   # channel-layer group_send smoke test
open tests/test_websocket.html             # browser-based socket inspector
```

`tests/requests.http` contains ready-made REST calls for the VS Code REST Client extension.

### Production Notes

- Run with `DJANGO_SETTINGS_MODULE=core.settings.production` for HSTS, SSL redirect, secure cookies, and `DATABASE_URL`-driven database config. `core/asgi.py` currently hardcodes `core.settings.base`, which has `DEBUG = True` — override the environment variable and gate `DEBUG` off the environment before deploying.
- `core/celery.py` hardcodes `broker_url`/`result_backend` to `redis://127.0.0.1:6379/0`, overriding the `CELERY_BROKER_URL` computed from `REDIS_URL`. Remove those two lines (or point them at the env var) before running workers on a separate host.
- `development.py` swaps in `InMemoryChannelLayer`, which does **not** fan out across processes. Keep the Redis layer any time more than one ASGI process is serving WebSockets.
- Generated audio is written to local disk under `MEDIA_ROOT/audio` and deleted after playback — flagged in the source as unsustainable at volume. The `boto3` dependency and AWS env keys are in place for an S3 migration.
