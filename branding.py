"""
Shared Creighton branding constants and helpers, used by both app.py and
every page under pages/. Keeping this in one file means every page stays
visually consistent without copy-pasting the same color codes everywhere.
"""
import streamlit as st

CU_BLUE = "#005CA9"
CU_NAVY = "#00235D"
CU_LIGHT_BLUE = "#6CADDE"
CU_SILVER = "#8A8D8F"
RESULT_COLORS = {"Win": "#2E7D32", "Draw": CU_SILVER, "Loss": "#9E2A2B"}


def section_header(text):
    st.markdown(f"<h2 style='color:{CU_NAVY};'>{text}</h2>", unsafe_allow_html=True)


def page_banner(title, subtitle):
    """Logo + title banner, matching the main dashboard's header style."""
    import os
    import base64

    if os.path.exists("logo.png"):
        with open("logo.png", "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode()
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; gap:24px; margin-bottom:8px;">
                <img src="data:image/png;base64,{logo_b64}" style="width:110px; height:auto;">
                <div>
                    <h1 style="color:{CU_NAVY}; margin:0; line-height:1.15;">{title}</h1>
                    <p style="color:{CU_BLUE}; font-size:0.95rem; margin:4px 0 0 0;">{subtitle}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(f"<h1 style='color:{CU_NAVY}; margin-bottom:0;'>{title}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:{CU_BLUE}; font-size:0.95rem; margin-top:0;'>{subtitle}</p>", unsafe_allow_html=True)


def page_footer():
    st.markdown("---")
    st.markdown(
        f"<p style='color:{CU_BLUE}; font-size:0.85rem;'>Built by Brooke — Business Intelligence Analytics & Marketing, Creighton University</p>",
        unsafe_allow_html=True,
    )
