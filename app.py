"""IISc Alumni Store — Streamlit entrypoint.

A capstone demonstration of an AI-enabled alumni merchandise portal.
Everything (catalog, cart, checkout, orders, profile) is mocked from JSON
files; the floating chatbot is the only component that calls a real,
remote API Gateway (configured in config.yaml / .env).

Run with:
    streamlit run app.py
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from chatbot.chat_ui import render_chatbot
from components.footer import render_footer
from components.navbar import render_navbar
from config import settings
from pages import about, cart, catalog, checkout, home, login, orders, product, profile
from utils.helpers import get_logger, init_state

log = get_logger()

ROUTES = {
    "home": home.render,
    "catalog": catalog.render,
    "product": product.render,
    "cart": cart.render,
    "checkout": checkout.render,
    "orders": orders.render,
    "profile": profile.render,
    "about": about.render,
}


def load_css() -> None:
    css_path = Path(__file__).parent / "styles" / "styles.css"
    try:
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>",
                    unsafe_allow_html=True)
    except OSError as exc:
        log.warning("Could not load stylesheet: %s", exc)


def main() -> None:
    st.set_page_config(
        page_title=settings.app_title,
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    init_state()
    load_css()

    if not st.session_state.authenticated:
        login.render()
        return

    render_navbar()

    page = st.session_state.page
    render = ROUTES.get(page)
    if render is None:
        log.error("Unknown route '%s', falling back to home", page)
        st.session_state.page = "home"
        render = home.render

    try:
        render()
    except Exception:  # noqa: BLE001 — last-resort guard so the demo never dies
        log.exception("Unhandled error rendering page '%s'", page)
        st.error("Something went wrong rendering this page. Please try again.")

    render_footer()
    render_chatbot()


if __name__ == "__main__":
    main()
