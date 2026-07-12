"""AI Assistant — the capstone's headline feature.

A prominent launcher pill sits fixed at the bottom-right of every page
(styled via the .st-key-chat_launcher CSS hook). Clicking it opens the
conversation inline as an anchored floating panel (st.popover) — the
page underneath stays visible and interactive, so it reads as part of
the storefront chrome rather than an interruption.

Message sends run in widget callbacks so the panel stays open across
turns; every message goes to the remote API Gateway via chatbot.api_client.
An {"intent": "escalate"} response triggers the support-ticket flow.
"""
from __future__ import annotations

import html
import random
import string

import streamlit as st

from chatbot.api_client import UNAVAILABLE_MESSAGE, send_message
from chatbot.models import ChatResponse
from config import settings
from utils.constants import CHAT_QUICK_ACTIONS, TICKET_RESPONSE_TIME
from utils.helpers import get_device_type, get_logger

log = get_logger("alumni_store.chat_ui")


def _new_ticket(response: ChatResponse) -> dict:
    ticket = response.ticket or {}
    return {
        "number": ticket.get(
            "number", "TCK-" + "".join(random.choices(string.digits, k=6))
        ),
        "response_time": ticket.get("response_time", TICKET_RESPONSE_TIME),
    }


def _push(role: str, content: str, meta: dict | None = None) -> None:
    st.session_state.chat_history.append(
        {"role": role, "content": content, "meta": meta or {}}
    )


def _send(message: str) -> None:
    """Send a message through the gateway; runs inside a widget callback."""
    message = message.strip()
    if not message:
        return
    _push("user", message)

    response = send_message(
        st.session_state.chat_session_id,
        st.session_state.user_id,
        message,
        get_device_type(),
    )

    if not response.ok:
        _push("bot", UNAVAILABLE_MESSAGE, {"error": True})
        return

    if response.is_escalation:
        ticket = _new_ticket(response)
        st.session_state.last_ticket = ticket
        reply = response.reply or "I've raised this with our support team."
        _push("bot", reply, {"escalated": True, "ticket": ticket})
        return

    _push("bot", response.reply or "…", {"intent": response.intent})


# --------------------------------------------------------------------------- #
# Widget callbacks (run before the rerun, so the dialog stays open)
# --------------------------------------------------------------------------- #
def _on_form_send() -> None:
    _send(st.session_state.get("chat_text", ""))


def _on_quick_action(prompt: str) -> None:
    _send(prompt)


def _on_clear() -> None:
    st.session_state.chat_history = []


# --------------------------------------------------------------------------- #
# Panel
# --------------------------------------------------------------------------- #
def _render_history() -> None:
    if not st.session_state.chat_history:
        st.markdown(
            "<div class='chat-bot'>Namaste! I can track orders, explain products, "
            "suggest gifts, or connect you to support. How can I help?</div>",
            unsafe_allow_html=True,
        )
        return

    for msg in st.session_state.chat_history[-30:]:
        safe = html.escape(msg["content"]).replace("\n", "<br>")
        if msg["role"] == "user":
            st.markdown(f"<div class='chat-user'>{safe}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='chat-bot'>{safe}</div>", unsafe_allow_html=True)
            meta = msg.get("meta", {})
            if meta.get("escalated"):
                ticket = meta["ticket"]
                st.success(
                    f"**Support Ticket Created**\n\n"
                    f"Ticket number: `{ticket['number']}`\n\n"
                    f"Expected response time: {ticket['response_time']}"
                )


def _chat_panel() -> None:
    # Streamlit portals the popover body outside .st-key-chat_launcher, so this
    # marker lets styles.css scope itself via :has() instead of descendant nesting.
    st.markdown("<div class='chat-panel-marker'></div>", unsafe_allow_html=True)
    st.markdown("**Alumni Store Assistant**")
    st.caption(
        "Connected to the Alumni Store API Gateway · "
        "I can track orders, answer product questions, and raise support tickets."
    )

    with st.container(height=340, border=False):
        _render_history()

    if not st.session_state.chat_history:
        st.markdown("<div class='chat-agent'>Try asking</div>", unsafe_allow_html=True)
        qa_cols = st.columns(2)
        for i, prompt in enumerate(CHAT_QUICK_ACTIONS):
            qa_cols[i % 2].button(
                prompt,
                key=f"qa_{i}",
                width="stretch",
                on_click=_on_quick_action,
                args=(prompt,),
            )

    with st.form("chat_form", clear_on_submit=True, border=False):
        st.text_input(
            "Message",
            key="chat_text",
            placeholder="e.g. Where is order IISC202600145?",
            label_visibility="collapsed",
        )
        st.form_submit_button("Send", type="primary", on_click=_on_form_send,
                              width="stretch")

    if st.session_state.chat_history:
        st.button("Clear conversation", key="chat_clear", on_click=_on_clear)


def render_chatbot() -> None:
    """Render the fixed launcher; opens an anchored panel in place. Call once per run."""
    if not settings.enable_chatbot:
        return
    with st.popover("💬 Ask the Assistant", key="chat_launcher"):
        _chat_panel()
