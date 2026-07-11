"""Home — hero with campus imagery, auto-rotating banner carousel, categories."""
from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

import streamlit as st

from components.product_card import render_product_card
from utils.constants import CATEGORIES
from utils.helpers import get_announcements, get_logger, get_products, go_to

log = get_logger("alumni_store.home")

PROJECT_ROOT = Path(__file__).resolve().parent.parent

BANNERS = (
    "assets/banner_1.jpg",
    "assets/banner_2.jpg",
    "assets/banner_3.jpg",
    "assets/banner_4.jpg",
)
SECONDS_PER_SLIDE = 5


@lru_cache(maxsize=16)
def _b64(rel_path: str) -> str:
    """Base64-encode a local image for inline HTML embedding."""
    try:
        return base64.b64encode((PROJECT_ROOT / rel_path).read_bytes()).decode()
    except OSError as exc:
        log.warning("Could not embed image %s: %s", rel_path, exc)
        return ""


def _render_hero() -> None:
    """Hero: merchandise pitch on the left, campus picture on the right.

    The campus image is a generated placeholder — drop a real photograph at
    assets/campus.jpg to replace it, nothing else changes.
    """
    campus = _b64("assets/campus.jpg")
    st.markdown(
        f"""
        <div class="hero hero-split">
          <div class="hero-text">
            <div class="kicker">Official Alumni Merchandise</div>
            <h1>Carry the Institute<br>with you.</h1>
            <p>Apparel, drinkware and memorabilia designed for IIScians —
            every purchase funds student scholarships.</p>
          </div>
          <div class="hero-media">
            <img src="data:image/jpeg;base64,{campus}" alt="IISc campus" />
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_carousel() -> None:
    """Banner carousel that crossfades automatically — no controls needed."""
    slides = [(_b64(p), i) for i, p in enumerate(BANNERS)]
    cycle = SECONDS_PER_SLIDE * len(BANNERS)
    imgs = "\n".join(
        f'<img src="data:image/jpeg;base64,{data}" '
        f'style="animation-delay:{i * SECONDS_PER_SLIDE}s" alt="banner {i + 1}" />'
        for data, i in slides
        if data
    )
    st.markdown(
        f"""
        <div class="carousel" style="--cycle:{cycle}s">
          {imgs}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render() -> None:
    _render_hero()
    _render_carousel()

    # ---- browse by category ----
    st.markdown("## Browse by category")
    st.markdown("<div class='crest-rule'></div>", unsafe_allow_html=True)
    products = get_products()
    cat_cols = st.columns(len(CATEGORIES) - 1)
    for col, category in zip(cat_cols, CATEGORIES[1:]):
        count = sum(1 for p in products if p["category"] == category)
        with col:
            if st.button(
                f"{category}\n\n{count} items",
                key=f"cat_{category}",
                width="stretch",
            ):
                st.session_state.catalog_category = category
                go_to("catalog")
                st.rerun()

    # ---- featured products ----
    st.markdown("## Featured this month")
    st.markdown("<div class='crest-rule'></div>", unsafe_allow_html=True)
    featured = sorted(products, key=lambda p: p["rating"], reverse=True)[:4]
    for col, product in zip(st.columns(4), featured):
        with col:
            render_product_card(product, key_prefix="home")

    # ---- announcements + quick links ----
    left, right = st.columns([2, 1])
    with left:
        st.markdown("## Latest announcements")
        st.markdown("<div class='crest-rule'></div>", unsafe_allow_html=True)
        for item in get_announcements():
            with st.container(border=True):
                st.markdown(f"**{item['title']}**")
                st.caption(item["date"])
                st.write(item["body"])

    with right:
        st.markdown("## Quick links")
        st.markdown("<div class='crest-rule'></div>", unsafe_allow_html=True)
        links = {
            "Shop the Catalog": "catalog",
            "Track an order": "orders",
            "Your cart": "cart",
            "Your profile": "profile",
            "About the store & FAQs": "about",
        }
        for label, target in links.items():
            if st.button(label, key=f"ql_{target}", width="stretch"):
                go_to(target)
                st.rerun()
        st.info(
            "Meet the **AI assistant** — the maroon button at the bottom-right "
            "opens it front and centre. Ask it to track an order or suggest a gift."
        )
