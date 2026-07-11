"""Catalog — full merchandise grid with search, category filter and sorting."""
from __future__ import annotations

import streamlit as st

from components.product_card import render_product_card
from utils.constants import CATEGORIES
from utils.helpers import get_products


def render() -> None:
    st.markdown("# Merchandise Catalog")
    st.markdown("<div class='crest-rule'></div>", unsafe_allow_html=True)

    default_cat = st.session_state.pop("catalog_category", "All")
    incoming_query = st.session_state.pop("catalog_query", "")

    search_col, cat_col, sort_col = st.columns([2.4, 1.4, 1.4])
    query = search_col.text_input(
        "Search products", value=incoming_query, placeholder="hoodie, mug, badge…"
    )
    category = cat_col.selectbox(
        "Category", CATEGORIES, index=CATEGORIES.index(default_cat)
    )
    sort_by = sort_col.selectbox(
        "Sort by", ("Popularity", "Price: low to high", "Price: high to low", "Rating")
    )

    products = get_products()
    if category != "All":
        products = [p for p in products if p["category"] == category]
    if query.strip():
        q = query.strip().lower()
        products = [
            p for p in products
            if q in p["name"].lower() or q in p["short_description"].lower()
        ]

    sorters = {
        "Popularity": lambda p: -p["reviews_count"],
        "Price: low to high": lambda p: p["price"],
        "Price: high to low": lambda p: -p["price"],
        "Rating": lambda p: -p["rating"],
    }
    products = sorted(products, key=sorters[sort_by])

    st.caption(f"{len(products)} product(s)")
    if not products:
        st.warning("No products match your search. Try a different term or category.")
        return

    for row_start in range(0, len(products), 4):
        row = products[row_start : row_start + 4]
        for col, product in zip(st.columns(4), row):
            with col:
                render_product_card(product, key_prefix="catalog")
