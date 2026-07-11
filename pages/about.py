"""About — purpose, mission, benefits, FAQs and support."""
from __future__ import annotations

import streamlit as st

from utils.helpers import get_faq


def render() -> None:
    st.markdown("# About the Alumni Store")
    st.markdown("<div class='crest-rule'></div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("### Purpose")
        st.write(
            "The IISc Alumni Store is the official home for Institute merchandise — "
            "a way for alumni, students, faculty and staff to carry a piece of "
            "campus wherever their work takes them."
        )
        st.markdown("### Mission")
        st.write(
            "Every rupee of surplus is returned to the community: funding "
            "student scholarships, supporting campus heritage restoration, and "
            "underwriting alumni chapter events across the world."
        )

    st.markdown("### Why shop here")
    b1, b2, b3 = st.columns(3)
    benefits = [
        ("Give back", "Surplus funds scholarships and heritage restoration."),
        ("Made to last", "Small-batch production with quality checks on every run."),
        ("Alumni perks", "Reward points, member pricing and early access drops."),
    ]
    for col, (title, body) in zip((b1, b2, b3), benefits):
        with col, st.container(border=True):
            st.markdown(f"**{title}**")
            st.write(body)

    st.markdown("### Frequently asked questions")
    st.markdown("<div class='crest-rule'></div>", unsafe_allow_html=True)
    for item in get_faq():
        with st.expander(item["q"]):
            st.write(item["a"])

    st.markdown("### Support")
    with st.container(border=True):
        st.write(
            "Fastest route: ask the AI assistant (bottom-right) — it can track "
            "orders, explain policies, and raise a support ticket for anything "
            "it can't resolve."
        )
        st.markdown(
            "- Email: `store@alumni.iisc.ac.in` (demo)\n"
            "- Phone: `+91 80 2293 XXXX`, Mon–Fri, 10:00–18:00 IST\n"
            "- Returns: within 14 days of delivery, unused and in original packaging"
        )
