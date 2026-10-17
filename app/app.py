"""Shelf-Sense web app router. Run: streamlit run app/app.py

Three pages share one navbar, stylesheet and footer:
  /              landing page          app/views/home.py
  /inspect       dashboard             app/views/inspect.py
  /how-it-works  method and evidence   app/views/method.py

Navigation uses st.page_link, so it happens client-side and an inspection result in session state
survives moving between pages.
"""

import sys
from pathlib import Path

# `streamlit run app/app.py` puts app/ first on sys.path; put the repo root first so
# `import app` resolves to the package, not to this file.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st  # noqa: E402

from app import site, ui  # noqa: E402

VIEWS = Path(__file__).resolve().parent / "views"

st.set_page_config(page_title="Shelf-Sense", layout="wide", initial_sidebar_state="collapsed")

home = st.Page(VIEWS / "home.py", title="Shelf-Sense · Shelf compliance from one photograph", default=True)
inspect = st.Page(VIEWS / "inspect.py", title="Dashboard · Shelf-Sense", url_path="inspect")
method = st.Page(VIEWS / "method.py", title="How it works · Shelf-Sense", url_path="how-it-works")
page = st.navigation([home, inspect, method], position="hidden")

st.markdown(ui.style_tag() + site.style_tag(), unsafe_allow_html=True)

with st.container(key="nav"):
    brand, links, cta = st.columns([3, 6, 2], vertical_alignment="center")
    brand.markdown(site.nav_brand(), unsafe_allow_html=True)
    with links, st.container(key="navlinks"):
        a, b, c, _ = st.columns([1, 1, 1, 1])
        a.page_link(home, label="Product")
        b.page_link(method, label="How it works")
        c.page_link(inspect, label="Dashboard")
    with cta, st.container(key="navcta"):
        st.page_link(inspect, label="Start inspecting →", use_container_width=True)

page.run()

st.markdown(site.footer(), unsafe_allow_html=True)
