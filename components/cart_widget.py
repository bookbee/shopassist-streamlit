"""Order summary widget shared by the Cart and Checkout pages."""
from __future__ import annotations

import streamlit as st

from utils.constants import FREE_SHIPPING_THRESHOLD
from utils.helpers import cart_totals, inr


def render_cart_summary(title: str = "Order Summary") -> dict:
    """Render subtotal / GST / shipping / total. Returns the totals dict."""
    totals = cart_totals()
    with st.container(border=True):
        st.markdown(f"#### {title}")
        row = lambda label, value: st.markdown(  # noqa: E731
            f"<div style='display:flex;justify-content:space-between'>"
            f"<span>{label}</span><strong>{value}</strong></div>",
            unsafe_allow_html=True,
        )
        row("Subtotal", inr(totals["subtotal"]))
        row("GST (18%)", inr(totals["gst"]))
        row("Shipping", "Free" if totals["shipping"] == 0 else inr(totals["shipping"]))
        st.divider()
        row("Total", inr(totals["total"]))

        if 0 < totals["subtotal"] < FREE_SHIPPING_THRESHOLD:
            remaining = FREE_SHIPPING_THRESHOLD - totals["subtotal"]
            st.caption(f"Add {inr(remaining)} more for free shipping.")
    return totals
