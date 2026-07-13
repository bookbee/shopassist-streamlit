"""Optional local mock of the remote API Gateway (stdlib only, no deps).

The Streamlit app's chatbot POSTs to {API_BASE_URL}/api/v1/chat. In production
that URL points at a real gateway; for local end-to-end demos, run this file
in a second terminal:

    python mock_gateway.py            # serves http://localhost:8000

It answers the capstone's demo scenarios with simple keyword routing and
returns {"intent": "escalate", "ticket": {...}} for support hand-offs, which
triggers the ticket UI in the app. Replace this with the real gateway by
changing API_BASE_URL in .env — the Streamlit app needs no code changes.
"""
from __future__ import annotations

import json
import re
from http.server import BaseHTTPRequestHandler, HTTPServer

HOST, PORT = "localhost", 8000

PRODUCT_FACTS = {
    "hoodie": "The Alumni Hoodie is 80% cotton / 20% polyester fleece at 320 GSM, "
              "brushed inside, with an embroidered chest wordmark. Sizes S–XXL.",
    "t-shirt": "The Classic T-Shirt is 100% combed cotton, 180 GSM, bio-washed, "
               "with a screen-printed gold crest. Sizes S–XXL.",
    "mug": "The Crest Ceramic Mug holds 330 ml and is microwave and dishwasher safe.",
    "flask": "The Insulated Coffee Flask keeps drinks hot 12 hours and cold 24 hours (500 ml).",
    "bottle": "The Steel Water Bottle is 750 ml, food-grade 304 stainless steel, "
              "leak-proof but not insulated.",
}

GIFTS_UNDER_1000 = (
    "Under ₹1000, alumni favourites are: the Alumni Lapel Badge (₹299), "
    "Tata Hall Notebook (₹249), Crest Ceramic Mug (₹349), Heritage Cap (₹449), "
    "Classic T-Shirt (₹599), and the Executive Pen Set (₹999) if you want a boxed gift."
)

SIZE_GUIDE = (
    "Our apparel runs true to size with a relaxed fit. Chest measurements: "
    "S 38\", M 40\", L 42\", XL 44\", XXL 46\". If you're between sizes on the "
    "t-shirt, size down; for the hoodie, stay with your usual size."
)


def route(message: str) -> dict:
    """Very small intent router for demo purposes."""
    text = message.lower()

    order_match = re.search(r"iisc\d{9,}", text)
    if order_match or "where is my order" in text or "track" in text:
        order_id = order_match.group(0).upper() if order_match else "your latest order"
        return {
            "intent": "track_order",
            "reply": f"Order {order_id} is out for delivery and should reach you "
                     "by tomorrow evening. You'll get an SMS when the courier is nearby.",
        }

    if "escalate" in text or "human" in text or "customer support" in text or "talk to" in text:
        return {
            "intent": "escalate",
            "reply": "I've connected you to our support team — a specialist will "
                     "take it from here.",
            "ticket": {"number": "TCK-482913", "response_time": "within 24 hours"},
        }

    if "return" in text or "refund" in text:
        return {
            "intent": "returns",
            "reply": "You can return any unused item within 14 days of delivery. "
                     "Go to Orders → select the order → Return, or share the order "
                     "ID here and I'll start it for you. Refunds land in 5–7 business days.",
        }

    if "payment" in text and ("fail" in text or "declin" in text or "stuck" in text):
        return {
            "intent": "payment",
            "reply": "Sorry about that — failed payments auto-reverse within 3–5 "
                     "business days and no order is created. If the amount was "
                     "debited, share the transaction reference and I'll flag it.",
        }

    if "size" in text:
        return {"intent": "size_guide", "reply": SIZE_GUIDE}

    if "deliver" in text or "arrive" in text or "shipping" in text:
        return {
            "intent": "delivery",
            "reply": "Metro cities take 3–5 business days; the rest of India 5–8. "
                     "Orders above ₹999 ship free.",
        }

    if "gift" in text or "suggest" in text or "recommend" in text or "below" in text:
        return {"intent": "recommendation", "reply": GIFTS_UNDER_1000}

    for keyword, fact in PRODUCT_FACTS.items():
        if keyword in text:
            return {"intent": "product_info", "reply": fact}

    if any(g in text for g in ("hello", "hi", "hey", "namaste")):
        return {
            "intent": "greeting",
            "reply": "Hello! I'm the Alumni Store assistant. I can track orders, "
                     "answer product questions, help with returns, or suggest gifts. "
                     "What can I do for you?",
        }

    return {
        "intent": "fallback",
        "reply": "I can help with order tracking, product details, sizing, delivery, "
                 "returns, payments, and gift ideas. Could you rephrase, or say "
                 "'customer support' to reach a human?",
    }


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):  # noqa: N802 — http.server API
        if self.path != "/api/v1/chat":
            self.send_error(404, "Unknown endpoint")
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length) or b"{}")
            message = str(payload.get("text", ""))
        except (ValueError, json.JSONDecodeError):
            self.send_error(400, "Invalid JSON")
            return

        print(
            f"[mock-gateway] session={payload.get('session_id')} "
            f"user={payload.get('user_id')} device={payload.get('device_type')}"
        )
        body = json.dumps(route(message)).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):  # quieter console
        print(f"[mock-gateway] {fmt % args}")


if __name__ == "__main__":
    print(f"Mock API Gateway listening on http://{HOST}:{PORT}/api/v1/chat")
    HTTPServer((HOST, PORT), Handler).serve_forever()
