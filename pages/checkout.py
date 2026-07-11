"""Checkout — mocked flow: address → payment → summary → confirmation."""
from __future__ import annotations

import streamlit as st

from components.cart_widget import render_cart_summary
from utils.helpers import (
    cart_items,
    estimated_delivery,
    generate_order_id,
    get_logger,
    go_to,
    inr,
)

log = get_logger("alumni_store.checkout")


def _render_success() -> None:
    checkout = st.session_state.checkout
    st.balloons()
    st.markdown("# Order Successful 🎉")
    st.markdown("<div class='crest-rule'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown(f"### Order ID: `{checkout['order_id']}`")
        st.markdown(f"**Estimated delivery:** {checkout['eta']}")
        st.write(
            "A confirmation email with your invoice is on its way. "
            "You can track this order any time from the Orders page — or just "
            "ask the assistant: *“Where is my order?”*"
        )
    col1, col2 = st.columns(2)
    if col1.button("View Orders", type="primary", width="stretch"):
        go_to("orders")
        st.rerun()
    if col2.button("Continue Shopping", width="stretch"):
        go_to("catalog")
        st.rerun()


def render() -> None:
    if st.session_state.checkout.get("step") == "done":
        _render_success()
        return

    lines = cart_items()
    if not lines:
        st.info("Nothing to check out yet — your cart is empty.")
        if st.button("Browse the Catalog", type="primary"):
            go_to("catalog")
            st.rerun()
        return

    st.markdown("# Checkout")
    st.markdown("<div class='crest-rule'></div>", unsafe_allow_html=True)

    form_col, summary_col = st.columns([2.2, 1], gap="large")

    with form_col:
        profile = st.session_state.profile
        addresses = profile.get("addresses", [])

        st.markdown("### Delivery Address")
        with st.container(border=True):
            labels = [
                f"{a['label']} — {a['line1']}, {a['city']} {a['pincode']}"
                for a in addresses
            ] + ["Add a new address"]
            choice = st.radio("Deliver to", labels, label_visibility="collapsed")
            if choice == "Add a new address":
                st.text_input("Full name", value=profile.get("name", ""))
                st.text_input("Address line 1")
                st.text_input("Address line 2")
                col_a, col_b, col_c = st.columns(3)
                col_a.text_input("City")
                col_b.text_input("State")
                col_c.text_input("PIN code")

        st.markdown("### Payment Method")
        with st.container(border=True):
            method = st.radio(
                "Pay with",
                ("UPI", "Credit / Debit Card", "Net Banking", "Cash on Delivery"),
                label_visibility="collapsed",
            )
            st.caption(
                "This is a demonstration checkout — no payment is collected "
                "and no card or UPI details are requested."
            )

        st.markdown("### Order Summary")
        with st.container(border=True):
            for line in lines:
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between'>"
                    f"<span>{line['product']['name']} × {line['qty']}</span>"
                    f"<strong>{inr(line['line_total'])}</strong></div>",
                    unsafe_allow_html=True,
                )

    with summary_col:
        totals = render_cart_summary(title="Payable")
        if st.button(
            f"Place Order · {inr(totals['total'])}",
            type="primary",
            width="stretch",
        ):
            order_id = generate_order_id()
            st.session_state.checkout = {
                "step": "done",
                "order_id": order_id,
                "eta": estimated_delivery(),
            }
            log.info("Mock order placed: %s via %s (%s)", order_id, method, totals["total"])
            st.session_state.cart = {}
            st.rerun()
        if st.button("← Back to Cart", width="stretch"):
            go_to("cart")
            st.rerun()
