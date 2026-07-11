"""Shared page footer."""
from __future__ import annotations

import streamlit as st


def render_footer() -> None:
    st.markdown(
        """
        <div class="footer">
          <div class="crest-rule"></div>
          <strong>IISc Alumni Store</strong> · Indian Institute of Science, Bengaluru 560012<br>
          Every purchase funds student scholarships and campus heritage restoration.<br>
          <span class="muted">Capstone demonstration · catalogue, orders and checkout are mocked ·
          the AI assistant connects to a live API Gateway</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
