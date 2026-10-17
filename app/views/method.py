"""How it works page (/how-it-works): pipeline, money, evaluation, limits."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st  # noqa: E402

from app import site  # noqa: E402


def html(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


html(site.method_head())
html(site.method_flow())
html(site.method_money())
html(site.method_evaluation())
html(site.method_limits())
html('<div class="ss-final" style="margin-top:72px;padding-top:72px"><span class="ss-eb">[ Try it ]</span>'
     '<div class="ss-final-h" style="margin-top:22px;font-size:clamp(40px,6vw,96px)">See it on<br><span>a real shelf.</span></div></div>')
with st.container(key="methodcta"):
    left, _ = st.columns([2, 5])
    left.page_link("views/inspect.py", label="Open the dashboard →", use_container_width=True)
