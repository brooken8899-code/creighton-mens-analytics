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


def current_roster_lastnames():
    """Last names of everyone on the TRUE 2026 roster (all 29 players, from
    gocreighton.com — not just the subset who've recorded minutes in a stats
    export), for filtering historical player tables down to names that are
    actually still relevant today. Falls back to player_stats_2026.csv if the
    full-roster file isn't present."""
    import pandas as pd
    try:
        current = pd.read_csv("roster_2026_full.csv")
    except FileNotFoundError:
        try:
            current = pd.read_csv("player_stats_2026.csv")
        except FileNotFoundError:
            return set()
    names = current["Player"].str.replace(r" \(.*\)", "", regex=True)
    return set(names.str.split().str[-1])


def full_roster_with_coverage():
    """The full 29-man 2026 roster, flagged with whether each player has shown
    up in any stats export yet. Returns None if roster_2026_full.csv is missing."""
    import pandas as pd
    try:
        return pd.read_csv("roster_2026_full.csv")
    except FileNotFoundError:
        return None


def roster_filter_toggle(label="Show only current 2026 roster players"):
    """Renders the on-by-default toggle. Returns (only_current: bool, roster_lastnames: set)."""
    only_current = st.checkbox(label, value=True)
    return only_current, current_roster_lastnames()


def is_on_roster(player_name, roster_lastnames):
    return player_name.split()[-1] in roster_lastnames


# (path, short label, description) — description is used on the Data Notes page.
# `in_nav` False keeps a page out of the top navigation (e.g. prototypes).
PAGE_DIRECTORY = [
    ("app.py", "🏠 Team", "Team-level patterns across seasons: finishing, home/away, pressing, style."),
    ("pages/11_2026_Under_the_Surface.py", "🔍 2026", "This season beneath the record: expected points, hidden contributors, formation, rotation, trend."),
    ("pages/9_2022_Beyond_Duncan.py", "🧩 2022", "What else besides Duncan McGuire's scoring stands out about 2022."),
    ("pages/2_Duncan_Blueprint.py", "⭐ Duncan", "Duncan McGuire's 2021→2022 numbers and which current attackers look similar."),
    ("pages/1_Player_Profiles.py", "👤 Players", "2026 per-90 leaders by position, with a 2021-2025 benchmark."),
    ("pages/6_Player_Consistency.py", "📊 Form", "How each 2026 player's output and role held up between the early and late windows."),
    ("pages/3_Style_and_Players.py", "🔗 Style", "How the 2026 team plays (possession, pressing) and who carries the passing."),
    ("pages/10_Data_Notes.py", "📝 Data Notes", "Where the data comes from, what it covers, and what it can't tell us."),
]

# Not shown in the top navigation (prototype with simulated data). Linked from Data Notes.
HIDDEN_PAGES = [
    ("pages/8_Workload_WhatIf.py", "⚡ Workload What-If", "Prototype: how GPS load data could pair with match output. Uses simulated load numbers."),
]


def page_nav(current_file):
    """Compact one-row navigation. The current page shows as plain bold text."""
    st.markdown(
        """<style>
        .block-container {max-width: 1350px; padding-top: 2rem;}
        div[data-testid="stPageLink"] a {padding: 2px 6px; font-size: 0.82rem; white-space: nowrap;}
        </style>""",
        unsafe_allow_html=True,
    )
    cols = st.columns([len(lbl) + 7 for _p, lbl, _d in PAGE_DIRECTORY])
    for col, (path, label, _desc) in zip(cols, PAGE_DIRECTORY):
        with col:
            if path == current_file:
                st.markdown(f"<span style='color:{CU_NAVY}; font-weight:700; font-size:0.85rem; border-bottom:2px solid {CU_BLUE};'>{label}</span>", unsafe_allow_html=True)
            else:
                st.page_link(path, label=label)


def finding(text, strength=None, n=None):
    """A headline-style callout: the takeaway in one or two sentences, with an
    optional evidence tag (e.g. strength='Moderate', n='83 matches')."""
    tag = ""
    if strength or n:
        bits = []
        if strength:
            bits.append(f"Evidence: {strength}")
        if n:
            bits.append(str(n))
        tag = f"<div style='color:{CU_SILVER}; font-size:0.8rem; margin-top:4px;'>{' · '.join(bits)}</div>"
    st.markdown(
        f"<div style='border-left:4px solid {CU_BLUE}; background:#F3F7FB; padding:10px 14px; margin:6px 0 12px 0;'>"
        f"<div style='color:{CU_NAVY}; font-size:1.0rem; font-weight:600;'>{text}</div>{tag}</div>",
        unsafe_allow_html=True,
    )


def short_name(full_name):
    """'Ayden Kokoszka' -> 'A. Kokoszka'. Names already abbreviated pass through."""
    parts = str(full_name).replace(" (", "|").split("|")[0].split()
    if len(parts) < 2:
        return str(full_name)
    if len(parts[0]) <= 2 and parts[0].endswith("."):
        return " ".join(parts)
    return f"{parts[0][0]}. {' '.join(parts[1:])}"


def pretty_cols(df):
    """Readable column headers for display tables: Goals_per90 -> 'Goals /90', DuelsWon_per90 -> 'Duels Won /90'."""
    import re

    def _p(c):
        c = str(c)
        c = c.replace("_per90", " /90").replace("_pct", " %").replace("_", " ")
        return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", c)

    return df.rename(columns=_p)


def _name_key(name):
    parts = str(name).split(" (")[0].split()
    return (parts[0][0], parts[-1])


def coverage_expander(log, min_matches, title="Which 2026 players are included?"):
    """Shows every 2026 outfield player with how many 2021-25 matches (20+ min) they have,
    and why anyone isn't in the tables above. `log` is player_match_log.csv as a DataFrame."""
    import pandas as pd
    try:
        cur = pd.read_csv("player_stats_2026.csv")
    except FileNotFoundError:
        return
    lg = log[log["Min"] >= 20].copy()
    lg["_k"] = lg["Player"].map(_name_key)
    counts = lg.groupby("_k").size()
    rows = []
    for _, r in cur.iterrows():
        k = _name_key(r["Player"])
        n = int(counts.get(k, 0))
        if n == 0:
            status = "No 2021–25 match data"
        elif n < min_matches:
            status = f"Below the {min_matches}-match minimum"
        else:
            status = "Included"
        rows.append({"Player": short_name(r["Player"]), "Position": r["PositionGroup"], "Matches 2021–25": n, "Status": status})
    t = pd.DataFrame(rows).sort_values(["Matches 2021–25"], ascending=False)
    n_new = int((t["Matches 2021–25"] == 0).sum())
    n_in = int((t["Status"] == "Included").sum())
    st.caption(
        f"{n_in} of {len(t)} current outfield players are included at this minimum. {n_new} have no match-by-match data from 2021–25 in this file (some may have been on the team, just not in these exports), "
        "so they will appear once a 2026 match-by-match export is available."
    )
    with st.expander(title):
        st.dataframe(t, use_container_width=True, hide_index=True)
