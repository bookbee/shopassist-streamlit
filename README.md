# IISc Alumni Store — AI-Enabled Merchandise Portal (Capstone Demo for group 2 - Shopassist)

A standalone Streamlit application that simulates the official **IISc Alumni
Merchandise Portal**. The entire e-commerce experience — catalog, cart,
checkout, orders, profile — is **mocked from local JSON files**. The one real
integration is the **floating AI assistant**, which talks to a remote **API
Gateway** over HTTP.


## Project Overview

| Page | What it demonstrates |
| --- | --- |
| Home | Hero, featured products, categories, announcements, quick links |
| Catalog | 12 mock products with search, category filter, sorting |
| Product Details | Large image, specs, reviews, quantity selector, recently viewed |
| Cart | Quantity updates, removal, subtotal + GST (18%) + shipping + total |
| Checkout | Address & payment selection (mocked), order summary, mock order ID (`IISC2026•••••`), success screen with estimated delivery |
| Orders | 6 mocked past orders with a tracking timeline and downloadable invoice |
| Profile | Mock alumni profile: department, graduation year, membership, addresses, reward points |
| About | Purpose, mission, benefits, FAQs, support channels |
| **AI Assistant** | Floating chat on every page; POSTs to the API Gateway; supports order tracking, product info, size guide, delivery, returns, payments, recommendations, greetings, and an **escalation flow** that creates a support ticket |

## Architecture

```
┌────────────────────────── Streamlit app ──────────────────────────┐
│  app.py ── router ── pages/ (home, catalog, product, cart, ...)   │
│              │                                                    │
│        components/ (navbar, footer, product_card, cart_widget)    │
│              │                                                    │
│        utils/ (helpers: state, cart math, logging · constants)    │
│              │                                                    │
│        data/*.json  ← ALL store data is mocked here               │
│                                                                   │
│  chatbot/chat_ui.py ── chatbot/api_client.py ──► HTTP POST ───────┼──►  API Gateway
│                        (the ONLY network call)   /api/chat        │     (remote / real)
└───────────────────────────────────────────────────────────────────┘
```

**Chat contract** — request:

```json
{ "session_id": "abc123", "message": "Where is my order?" }
```

Response (normal): `{ "reply": "...", "intent": "track_order" }`
Response (escalation): `{ "reply": "...", "intent": "escalate", "ticket": { "number": "TCK-482913", "response_time": "within 24 hours" } }`

When `intent == "escalate"`, the UI shows **Support Ticket Created** with the
ticket number and expected response time. If the gateway is down, times out,
or returns malformed JSON, the chat shows *“AI Assistant is currently
unavailable.”* and the app never crashes.


## Installation

Requires **Python 3.12** (3.10+ works).

```bash
<go to your working directory>
git clone https://github.com/bookbee/shopassist-streamlit
cd shopassist-streamlit
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Running

```bash
streamlit run app.py
```

Optionally, for a full end-to-end chatbot demo without the real gateway, run
the included stdlib mock in a **second terminal**:

```bash
python mock_gateway.py     # serves http://localhost:8600/api/chat
```

Then open the app, click **💬 Ask the Assistant**, and try:

- `Where is order IISC202600145?`
- `What material is the hoodie?`
- `What size should I buy?`
- `Suggest gifts below ₹1000`
- `I want to talk to customer support` → triggers the ticket flow

## Configuration

All configurable values live outside the code:

| Key | Where | Default | Purpose |
| --- | --- | --- | --- |
| `API_BASE_URL` | `.env` / `config.yaml` | `http://localhost:8600` | Gateway base URL |
| `CHAT_ENDPOINT` | `.env` / `config.yaml` | `/api/chat` | Chat path |
| `TIMEOUT` | `.env` / `config.yaml` | `10` | Request timeout (s) |
| `APP_TITLE` | `.env` / `config.yaml` | `IISc Alumni Store` | Browser title |
| `ENABLE_CHATBOT` | `.env` / `config.yaml` | `true` | Feature flag |
| `colors.*` | `config.yaml` | maroon / white / gold / gray | Palette |

Environment variables (or a `.env` file — see `.env.example`) override
`config.yaml`. To point the app at the real gateway, set `API_BASE_URL` only;
no code changes needed.

## Logging & Error Handling

- Rotating log at `logs/app.log` with INFO / WARNING / ERROR levels
  (navigation, cart actions, chat outcomes, gateway failures).
- The chatbot client converts **timeouts, connection failures, HTTP errors,
  and JSON parse errors** into a graceful in-chat message.
- A last-resort guard around page rendering shows a friendly alert instead of
  a stack trace.

## Project Structure

```
iisc_alumni_store/
├── app.py                  # entrypoint + router
├── config.py / config.yaml # settings (env-overridable)
├── mock_gateway.py         # optional local stand-in for the API Gateway
├── requirements.txt
├── assets/                 # generated logo, banner, product images
├── pages/                  # home, catalog, product, cart, checkout, orders, profile, about
├── chatbot/                # chat_ui, api_client, models
├── components/             # navbar, footer, product_card, cart_widget
├── data/                   # products, orders, profile, faq, announcements (JSON)
├── utils/                  # helpers, constants
├── styles/styles.css       # custom theme
└── logs/app.log
```

## Future Improvements

- Real authentication (alumni SSO) and member pricing
- Payment gateway integration at the mocked checkout step
- Replace `data/*.json` with a database + inventory service
- Streaming chat responses and typing indicator over SSE/WebSocket
- Wishlist persistence, dark mode, and internationalisation
- Image CDN with real product photography
- Create an image and push it to the dockerhub
