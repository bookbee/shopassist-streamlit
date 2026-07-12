"""Typed models for the chatbot layer."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ChatRequest:
    """Payload sent to the API Gateway."""

    session_id: str
    user_id: str
    text: str
    device_type: str

    def to_json(self) -> dict[str, str]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "text": self.text,
            "device_type": self.device_type,
        }


@dataclass
class ChatResponse:
    """Normalised response from the API Gateway.

    ok=False means the gateway was unreachable or returned garbage;
    the UI then shows the graceful "assistant unavailable" message.
    """

    ok: bool
    reply: str = ""
    intent: Optional[str] = None
    ticket: Optional[dict[str, Any]] = None
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def is_escalation(self) -> bool:
        return self.intent == "escalate"
