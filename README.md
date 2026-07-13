# IISc Alumni Store — AI-Enabled Merchandise Portal (Capstone Demo for group 2 - Shopassist)

A standalone Streamlit app simulating the IISc Alumni Merchandise Portal. The
storefront — catalog, cart, checkout, orders, profile — is entirely mocked
from local JSON files under `data/`. The one real integration is the
floating AI assistant, which talks to a remote API Gateway over plain HTTP.

Everything except the chat widget works with zero backend. The chat widget
needs *something* listening on `API_BASE_URL` — either the stdlib
`mock_gateway.py` included here, or the real `shopassist` FastAPI service
(same repo family, separate project) once it's running.

## Project overview

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
                       (the only network call anywhere in this app)
```

The gateway is whatever's listening at `API_BASE_URL` — swapping
`mock_gateway.py` for the real service is just changing that one value (they
both happen to default to port 8000, so most days you don't even change
that).

### Chat contract

This is copied field-for-field from the real shopassist backend's Pydantic
schemas, so `mock_gateway.py` and the real service are interchangeable
without touching any Streamlit code.

Request:

```json
{ "session_id": "abc123", "user_id": "alumni2018", "text": "Where is my order?", "source_channel": "web_chat" }
```

Response:

```json
{ "session_id": "abc123", "response_text": "...", "agent_invoked": "OrderTrackingAgent",
  "confidence_score": 0.9, "timestamp": "2026-07-13T10:15:00+00:00" }
```

`agent_invoked == "EscalationAgent"` is what triggers the support-ticket UI.
There's no `ticket` field in the response at all — the real backend doesn't
have one at the API layer, so the ticket number/response-time shown to the
customer is always made up client-side (`chatbot/chat_ui.py::_new_ticket`).
That's deliberate, not a shortcut: it means the ticket flow behaves
identically whether you're pointed at the mock or the real thing.

If the gateway is down, times out, or sends back garbage, the widget just
shows *"AI Assistant is currently unavailable."* — it never crashes the app.
While a reply is in flight you'll see a three-dot typing indicator in the
chat panel.

## Installation

Requires Python 3.12 (3.10+ should work).

```bash
git clone https://github.com/bookbee/shopassist-streamlit
cd shopassist-streamlit
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # defaults are fine for local dev
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
running; it currently needs a few things fixed before it boots).

## Configuration

Everything's read from `.env` (falls back to `config.yaml`, then a
hardcoded default). `.env` is gitignored — `.env.example` is what's actually
checked in:

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

A few things worth knowing before you go debugging from scratch:

- **The real gateway's greeting currently looks wrong.** It says things like
  "Hello session_x!" instead of using your actual name — that's
  `services/llm_inference.py::call_generative()` in the `shopassist` repo
  deriving a "name" from `session_id`, which was never meant to hold one.
  Not fixable from this repo; `mock_gateway.py` here does it properly
  (looks up `data/profile.json`) so you can see what it *should* look like.
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

## Project structure

```
shopassist-streamlit/
├── app.py                  entrypoint + router
├── config.py / config.yaml settings (env-overridable)
├── mock_gateway.py         local stand-in for the API Gateway
├── requirements.txt
├── .env.example
├── assets/                 logo, banner, product images
├── pages/                  login, home, catalog, product, cart, checkout, orders, profile, about
├── chatbot/                chat_ui, api_client, models
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
- Create an image and push it to the dockerhub
