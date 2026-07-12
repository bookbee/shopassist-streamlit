"""HTTP client for the remote chatbot API Gateway.

This is the only component in the application that talks to a real network
service. Everything else in the store is mocked. The gateway contract:

    POST {API_BASE_URL}/api/v1/chat
    -> {"session_id": "abc123", "user_id": "alumni2018", "text": "Where is my order?", "device_type": "desktop"}
    <- {"reply": "...", "intent": "track_order", ...}

If the response contains {"intent": "escalate"} the UI opens the support
ticket flow.
"""
from __future__ import annotations

import json

import requests

from chatbot.models import ChatRequest, ChatResponse
from config import settings
from utils.helpers import get_logger

log = get_logger("alumni_store.chat")

UNAVAILABLE_MESSAGE = "AI Assistant is currently unavailable."


def send_message(session_id: str, user_id: str, message: str, device_type: str) -> ChatResponse:
    """POST the user's message to the gateway and normalise the reply.

    Never raises — every failure mode collapses to ChatResponse(ok=False)
    so the UI can degrade gracefully instead of crashing.
    """
    request = ChatRequest(session_id=session_id, user_id=user_id, text=message, device_type=device_type)
    url = settings.chat_url
    log.debug("Sending message to %s: %s", url, request.to_json())
    try:
        response = requests.post(
            url,
            json=request.to_json(),
            timeout=settings.timeout_seconds,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
    except requests.exceptions.Timeout:
        log.warning("Chat gateway timeout after %ss (%s)", settings.timeout_seconds, url)
        return ChatResponse(ok=False)
    except requests.exceptions.ConnectionError:
        log.warning("Chat gateway unreachable (%s)", url)
        return ChatResponse(ok=False)
    except requests.exceptions.HTTPError as exc:
        log.error("Chat gateway HTTP error: %s", exc)
        return ChatResponse(ok=False)
    except requests.exceptions.RequestException as exc:
        log.error("Chat gateway request failed: %s", exc)
        return ChatResponse(ok=False)

    try:
        payload = response.json()
    except (json.JSONDecodeError, ValueError) as exc:
        log.error("Chat gateway returned invalid JSON: %s", exc)
        return ChatResponse(ok=False)

    if not isinstance(payload, dict):
        log.error("Chat gateway returned non-object JSON: %r", payload)
        return ChatResponse(ok=False)

    reply = str(payload.get("reply", "")).strip()
    intent = payload.get("intent")
    ticket = payload.get("ticket") if isinstance(payload.get("ticket"), dict) else None

    log.info("Chat ok | intent=%s | %d chars", intent, len(reply))
    return ChatResponse(ok=True, reply=reply, intent=intent, ticket=ticket, raw=payload)
