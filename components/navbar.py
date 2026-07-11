"""Store header: announcement strip + brand + live search + page navigation."""
from __future__ import annotations

import streamlit as st

from utils.constants import PAGES
from utils.helpers import cart_count, go_to


def _on_nav_search() -> None:
    """Route header searches to the catalog with the query applied."""
    query = st.session_state.get("nav_search", "").strip()
    if query:
        st.session_state.catalog_query = query
        st.session_state.nav_search = ""
        go_to("catalog")


def render_navbar() -> None:
    st.markdown(
        "<div class='utility-strip'>Free shipping on orders above <strong>₹999</strong> "
        "&nbsp;·&nbsp; Convocation 2026 Collection is live &nbsp;·&nbsp; "
        "Every purchase funds student scholarships</div>",
        unsafe_allow_html=True,
    )

    with st.container():
        st.markdown("<div class='nav-wrap'>", unsafe_allow_html=True)
        brand_col, search_col, *nav_cols = st.columns([1.9, 1.7] + [0.8] * len(PAGES))

        with brand_col:
            logo_col, text_col = st.columns([1, 3])
            logo_col.image("assets/logo.png", width=52)
            text_col.markdown(
                "<div class='brand-title'>Alumni Store</div>"
                "<div class='brand-sub'>Indian Institute of Science</div>",
                unsafe_allow_html=True,
            )

        search_col.text_input(
            "Search",
            key="nav_search",
            placeholder="🔍 Search merchandise…",
            label_visibility="collapsed",
            on_change=_on_nav_search,
        )

        current = st.session_state.page
        for col, (label, target) in zip(nav_cols, PAGES.items()):
            display = label
            if target == "cart" and cart_count():
                display = f"{label} ({cart_count()})"
            kind = "primary" if current == target else "secondary"
            if col.button(display, key=f"nav_{target}", type=kind, width="stretch"):
                go_to(target)
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
