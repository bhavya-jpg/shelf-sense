"""Landing page (/). Static marketing content; every figure on it is a recorded fact (app/site.py)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st  # noqa: E402

from app import site  # noqa: E402

INSPECT = "views/inspect.py"
METHOD = "views/method.py"


def html(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


html(site.hero_top())
lede, ctas = st.columns([7, 5], vertical_alignment="bottom", gap="large")
lede.markdown(site.hero_lede(), unsafe_allow_html=True)
with ctas:
    c1, c2 = st.columns([3, 2])
    with c1, st.container(key="herocta"):
        st.page_link(INSPECT, label="Start an inspection →", use_container_width=True)
    with c2, st.container(key="heroghost"):
        st.page_link(METHOD, label="How it works", use_container_width=True)

html(site.product_frame())
html(site.marquee(site.LANDING_MARQUEE))
html(site.problem_section())
html(site.how_section())
html(site.features_section())
html(site.evidence_section())
html(site.honest_section())
html(site.amd_section())
html(site.final_cta())
with st.container(key="finalcta"):
    left, _ = st.columns([2, 5])
    left.page_link(INSPECT, label="Open the dashboard →", use_container_width=True)
html(site.marquee(site.FOOT_MARQUEE, dark=True))
