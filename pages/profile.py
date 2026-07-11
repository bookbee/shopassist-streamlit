"""Profile — mock alumni profile with addresses, recent orders, reward points."""
from __future__ import annotations

import streamlit as st

from utils.helpers import get_orders, inr


def render() -> None:
    profile = st.session_state.profile

    st.markdown("# Your Profile")
    st.markdown("<div class='crest-rule'></div>", unsafe_allow_html=True)

    id_col, detail_col = st.columns([1, 2.4], gap="large")

    with id_col:
        with st.container(border=True):
            st.image(profile.get("avatar", "assets/logo.png"), width="stretch")
            st.markdown(f"### {profile.get('name', '—')}")
            st.markdown(
                f"<span class='badge badge-status'>{profile.get('membership', '')}</span>",
                unsafe_allow_html=True,
            )
            st.metric("Reward Points", profile.get("reward_points", 0))
            st.caption("100 points = ₹50 off a future order")
            if st.button("Edit Profile", width="stretch"):
                st.toast("Profile editing is mocked in this demo.", icon="✏️")

    with detail_col:
        with st.container(border=True):
            st.markdown("#### Alumni details")
            rows = {
                "Department": profile.get("department", "—"),
                "Degree": profile.get("degree", "—"),
                "Graduation year": profile.get("graduation_year", "—"),
                "Member since": profile.get("member_since", "—"),
                "Email": profile.get("email", "—"),
                "Phone": profile.get("phone", "—"),
            }
            for label, value in rows.items():
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between'>"
                    f"<span class='muted'>{label}</span><span>{value}</span></div>",
                    unsafe_allow_html=True,
                )

        st.markdown("#### Shipping addresses")
        addr_cols = st.columns(len(profile.get("addresses", [])) or 1)
        for col, addr in zip(addr_cols, profile.get("addresses", [])):
            with col, st.container(border=True):
                default = " · default" if addr.get("default") else ""
                st.markdown(f"**{addr['label']}**{default}")
                st.write(
                    f"{addr['line1']}, {addr['line2']}, "
                    f"{addr['city']}, {addr['state']} {addr['pincode']}"
                )

        st.markdown("#### Recent orders")
        for order in get_orders()[:3]:
            st.markdown(
                f"<div style='display:flex;justify-content:space-between'>"
                f"<span>`{order['order_id']}` · {order['date']}</span>"
                f"<span><strong>{inr(order['amount'])}</strong> — "
                f"{order['status']}</span></div>",
                unsafe_allow_html=True,
            )
