# shopassist-client

The web client for the ShopAssist platform — today, that's the "IISc
Alumni Store" merchandise portal demo (catalog, cart, checkout, orders,
profile) plus the floating AI assistant that talks to the `shopassist`
backend.

**Role, not implementation.** This repo's job is "be a web client for
ShopAssist" — the storefront and chat widget a customer sees in a
browser. It does not need to be Streamlit forever, and production almost
certainly won't be. See **Current state vs. production** below for
exactly what that means and what does or doesn't carry over.

## Current state vs. production

| | Capstone (now) | Production (later) |
|---|---|---|
| Built with | Streamlit — one Python process renders the whole UI | A real frontend: a React web app, and/or native iOS/Android clients |
| Storefront data | Mocked from local JSON in `data/` | A real product/order/inventory service |
| Chat integration | `chatbot/api_client.py` + `chatbot/models.py`, Streamlit-rendered by `chatbot/chat_ui.py` | Same API contract (below), reimplemented in whatever the client's own language/framework is |
| Auth | Any non-empty user ID/password — a gate, not real auth | Real alumni SSO |

**What's actually reusable when this becomes React or a native app is not
the Streamlit code** — React can't run a Streamlit component, and neither
can Swift/Kotlin. What *is* reusable, and is exactly what's meant to be
pluggable here:

1. **The chat API contract** — the JSON shapes in "Chat contract" below.
   Any client, in any language, that sends the same request and handles
   the same response fields talks to the same `shopassist` backend with
   zero backend changes.
2. **The behavioral rules** — when to show the escalation/ticket flow,
   that the ticket itself is always synthesised client-side, the
   first-turn-only personalized greeting, degrading to a plain "unavailable"
   message on any failure. These are product decisions, not Streamlit
   mechanics — a production client should replicate them, not reinvent them.
3. **`chatbot/api_client.py` and `chatbot/models.py` specifically** have
   zero Streamlit dependency today — plain `requests` and dataclasses. If
   a future Python-based frontend ever replaces Streamlit (unlikely, but
   possible), those two files are close to drop-in. `chatbot/chat_ui.py`
   is the one Streamlit-specific file — the rendering layer — and is what
   actually gets rewritten for React/native.

If you're building the production client, skip straight to **For UI
developers building the production client** below — it's written so you
never need to open a Streamlit file to get started.

## For UI developers building the production client

You need exactly one thing from this repo: the API contract below. Here's
the same `send_message` call from `chatbot/api_client.py`, as a React
`fetch` call, so you have a concrete starting point without reading any
Python:

```js
const UNAVAILABLE_MESSAGE = "AI Assistant is currently unavailable.";

async function sendMessage(sessionId, userId, text, sourceChannel = "web_chat") {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, user_id: userId, text, source_channel: sourceChannel }),
    });
    if (!res.ok) return { ok: false, reply: UNAVAILABLE_MESSAGE };

    const data = await res.json();
    return {
      ok: true,
      sessionId: data.session_id,       // persist this, send it back on the next turn
      reply: data.response_text,
      agentInvoked: data.agent_invoked,
      confidenceScore: data.confidence_score,
      isEscalation: data.agent_invoked === "EscalationAgent",
    };
  } catch {
    return { ok: false, reply: UNAVAILABLE_MESSAGE };  // network error, timeout, etc.
  }
}
```

Behavioral rules to carry over, regardless of framework:

- **`session_id` is opaque** — mint one client-side (a UUID) on first
  load, send it on every turn, keep using whatever the response echoes
  back. Never parse it for anything (see the fixed bug this repo used to
  have below).
- **On `isEscalation: true`**, show a "support ticket created" UI. The
  backend has no ticket number/response-time in its response at all —
  make one up client-side (a random reference, a fixed SLA string) and
  show it. This isn't a shortcut you're meant to remove later; the real
  backend genuinely has no ticket concept at the API layer.
- **Greet by name only on a session's first message**, not every turn —
  repeating a name in every reply reads as robotic. This demo's mock
  gateway does this correctly (looks up a real name); replicate the
  *pattern* (first-turn-only), not any specific lookup mechanism.
- **Any failure — timeout, non-2xx, malformed JSON — degrades to the same
  generic "unavailable" message.** Never surface a stack trace or raw
  error to the customer.
- **Show a typing/waiting indicator between send and reply.** The network
  call is not instant; a bare frozen input reads as broken.

## Chat contract

Copied field-for-field from the real `shopassist` backend's Pydantic
schemas (`api/schemas.py`), so `mock_gateway.py` here and the real service
are interchangeable without touching any client code, in this repo or a
future one.

Request:

```json
{ "session_id": "abc123", "user_id": "alumni2018", "text": "Where is my order?", "source_channel": "web_chat" }
```

Response:

```json
{ "session_id": "abc123", "response_text": "...", "agent_invoked": "OrderTrackingAgent",
  "confidence_score": 0.9, "timestamp": "2026-07-13T10:15:00+00:00" }
```

`agent_invoked == "EscalationAgent"` is what triggers the support-ticket
UI. There's no `ticket` field in the response at all — the real backend
doesn't have one at the API layer, so the ticket number/response-time
shown to the customer is always made up client-side
(`chatbot/chat_ui.py::_new_ticket`). That's deliberate, not a shortcut: it
means the ticket flow behaves identically whether you're pointed at the
mock or the real thing.

If the gateway is down, times out, or sends back garbage, the widget just
shows *"AI Assistant is currently unavailable."* — it never crashes the
app. While a reply is in flight you'll see a three-dot typing indicator in
the chat panel.

## Project overview (today's Streamlit implementation)

| Page | What it does |
| --- | --- |
| Login | Gates the app. Demo auth only — any non-empty user ID / password pair works, no accounts exist anywhere |
| Home | Hero, featured products, categories, announcements |
| Catalog | 12 mock products — search, category filter, sort |
| Product details | Images, specs, reviews, quantity picker, recently viewed |
| Cart | Qty updates, removal, subtotal + 18% GST + shipping + total |
| Checkout | Mocked address/payment, order summary, a fake order ID (`IISC2026•••••`), success screen with an ETA |
| Orders | 6 mocked past orders, a tracking timeline, downloadable invoice |
| Profile | Department, graduation year, membership, addresses, reward points — all from `data/profile.json` |
| About | Mission, FAQs, support channels |
| **AI Assistant** | Floating launcher on every page. Order tracking, product Q&A, sizing, delivery, returns, payments, gift recommendations, and an escalation flow that raises a support ticket |

## Architecture

```
app.py (router)
 ├─ pages/login.py     gate — nothing past this renders until authenticated
 ├─ pages/*.py         home, catalog, product, cart, checkout, orders, profile, about
 ├─ components/*       navbar, footer, product_card, cart_widget
 ├─ utils/*            session state defaults, cart math, logging
 └─ data/*.json        every bit of "backend" data the storefront uses

chatbot/chat_ui.py → chatbot/api_client.py → POST /api/v1/chat → API Gateway
  (Streamlit-      (plain Python, no      (the only network call
   specific;         Streamlit dependency   anywhere in this app)
   swap this for     — see "Current state
   React/native)     vs. production" above)
```

The gateway is whatever's listening at `API_BASE_URL` — swapping
`mock_gateway.py` for the real service is just changing that one value
(they both happen to default to port 8000, so most days you don't even
change that).

## Installation

Requires Python 3.12 (3.10+ should work).

```bash
git clone https://github.com/bookbee/shopassist-client
cd shopassist-client
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Running

```bash
streamlit run app.py
```

Log in with any user ID / password (it's a demo — nothing is checked).

The chat widget needs a gateway running on `API_BASE_URL`. For local demos,
run the included mock in a second terminal:

```bash
python mock_gateway.py     # serves http://localhost:8000/api/v1/chat
```

Then open the app, click **💬 Ask the Assistant**, and try:

- `Where is order IISC202600145?`
- `What material is the hoodie?`
- `What size should I buy?`
- `Suggest gifts below ₹1000`
- `I want to talk to customer support` → triggers the ticket flow

First message of a session gets a "Hi \<name\>!" greeting, pulled from
`data/profile.json` — after that it drops the name and just answers.

To point at the real gateway instead: stop `mock_gateway.py`, start the
`shopassist` FastAPI service on the same port, done — no code or config
change needed on this side (see that repo's README for how to get it
running).

## Running with Docker

`docker-compose.yml` and `Dockerfile` here build and run just this
container — standalone, the same way `shopassist`, `shopassist-database`,
and `shopassist-model` are each independently runnable. The image is
tagged `shopassist-client:latest` and the container is named
`shopassist-client`, consistently with the other three projects' own
`shopassist-<role>` naming (`shopassist-api`, `shopassist-model`,
`shopassist-database`).

```bash
docker compose up -d --build
```

It talks to the API on the host via `host.docker.internal` — start it
first (`cd ../shopassist && docker compose up -d`, or plain `uvicorn`)
before or after bringing this container up; it retries on its own.

To run the **whole platform** together (Postgres, Ollama, the API, and
this storefront) with one command, use
[shopassist-devops](../shopassist-devops) instead — it `include:`s this
file and wires the chat widget to talk to the API over a shared container
network rather than `host.docker.internal`.

## Configuration

Everything's read from `.env` (falls back to `config.yaml`, then a
hardcoded default). `.env` is gitignored; create one in the repo root with
these variables, adjusted as needed — defaults below are fine for local dev:

```env
API_BASE_URL=http://localhost:8000
TIMEOUT=10
APP_TITLE=IISc Alumni Store
ENABLE_CHATBOT=true
LOG_LEVEL=INFO
```

`config.yaml` also holds the storefront palette (`colors.primary/secondary/
accent/neutral`) and the chat endpoint path (`/api/v1/chat`) — those two
basically never need to change, which is why they're not in `.env`.

## Logging

- Rotating log at `logs/app.log` (INFO+ by default, `LOG_LEVEL=DEBUG` for
  more) — navigation, cart actions, chat outcomes, gateway failures.
- Every chat request/response round-trip is logged at DEBUG, request and
  response both, full body — handy when something's coming back from the
  real gateway in a shape this app doesn't expect.
- Chat failures (timeout, connection refused, HTTP error, bad JSON) all
  collapse to the same graceful in-chat message rather than an exception.

## Known issues / things that'll bite you

- **`mock_gateway.py` and a real `uvicorn` instance of the shopassist API
  can't both hold port 8000.** If chat requests are behaving weirdly, check
  `lsof -i :8000` for who's actually listening before assuming it's a code
  bug.
- **Don't `rm` `logs/app.log` while the app is running.** The running
  process still has the old file open and keeps writing to it — the
  filename you're looking at just silently stops updating. Restart the app
  if this happens.
- `config.py`'s hardcoded fallback for `API_BASE_URL` says port 8600 if
  neither `.env` nor `config.yaml` has a value — that's stale and never
  actually hit in this repo since `config.yaml` always wins. Worth cleaning
  up at some point, not urgent.

~~The real gateway's greeting derives a "name" from `session_id`~~ **fixed
upstream** — `shopassist`'s `call_generative()` now greets using a real
customer-name lookup, first-turn-only, matching the pattern this repo's
`mock_gateway.py` always used. See that repo's README if you want the detail.

## Project structure

```
shopassist-client/
├── app.py                  entrypoint + router
├── config.py / config.yaml settings (env-overridable)
├── mock_gateway.py         local stand-in for the API Gateway
├── requirements.txt
├── Dockerfile               builds the shopassist-client image (see "Running with Docker")
├── docker-compose.yml       standalone `docker compose up` for just this container
├── assets/                 logo, banner, product images
├── pages/                  login, home, catalog, product, cart, checkout, orders, profile, about
├── chatbot/                api_client.py + models.py (framework-agnostic) and chat_ui.py (Streamlit-specific)
├── components/             navbar, footer, product_card, cart_widget
├── data/                   products, orders, profile, faq, announcements — all JSON
├── utils/                  helpers, constants
├── styles/styles.css       theme + chat bubble/typing-indicator styles
└── logs/app.log
```

## Not done yet

- Real authentication (alumni SSO) and member pricing
- Payment gateway integration at the mocked checkout step
- `data/*.json` → a real database + inventory service (there's already a
  `shopassist-database` project in this family meant for exactly this)
- Token-by-token streaming over SSE/WebSocket (the typing indicator's here,
  but replies still land all at once, not word-by-word)
- Wishlist persistence, dark mode, i18n
- Real product photography instead of generated placeholders
- Publish the `shopassist-client` image to a registry (Docker Hub or
  otherwise) — it builds locally (see "Running with Docker") but isn't
  pushed anywhere yet
- The actual React/native production client this repo is a stand-in for
