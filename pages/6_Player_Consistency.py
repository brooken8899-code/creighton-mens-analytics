import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from branding import (CU_BLUE, CU_NAVY, CU_LIGHT_BLUE, CU_SILVER, page_banner, page_footer, page_nav,
                      section_header, finding, short_name, pretty_cols)

st.set_page_config(page_title="Creighton Bluejays — Player Form", layout="wide", page_icon="🔵")

page_banner("Player Form", "Men's Soccer &middot; How each 2026 player's output and role have held up through the season")
page_nav("pages/6_Player_Consistency.py")
st.markdown("---")

try:
    wl = pd.read_csv("player_2026_early_vs_late.csv")
    rot = pd.read_csv("rotation_2026.csv")
except FileNotFoundError as e:
    st.info(f"Missing file: {e.filename}")
    st.stop()

st.info(
    "**What this page can and can't show.** A true match-to-match consistency score needs each player's numbers from every 2026 match. "
    "The 2026 player data comes as two five-match windows (Aug 23 – Sep 8 and Sep 19 – Oct 3), so this page shows two things we can measure: "
    "how each player's output moved between the windows, and how steady each player's role has been. "
    "A 2026 match-by-match player export would unlock the full consistency view."
)

# ---------------------------------------------------------------------------
section_header("1. Is each player's output holding up, climbing or fading?")
st.markdown(
    "**Question:** Comparing the early window with the late window, whose per-90 numbers went up or down?"
)

no_late = wl[~wl["HasLateWindow"]]["Player"].map(short_name).tolist()
if no_late:
    st.caption(f"Not shown (no late-window minutes): {', '.join(no_late)}.")
c1, c2 = st.columns(2)
with c1:
    metric_choice = st.selectbox(
        "Metric", ["Passes_per90", "DuelsWon_per90", "RecoveriesOppHalf_per90", "Shots_per90", "Goals_per90"],
        format_func=lambda x: x.replace("_per90", "").replace("_", " ") + " per 90",
    )
with c2:
    min_late = st.slider("Minimum minutes in each window", 0, 300, 90, step=15)

early_col, late_col = f"Early_{metric_choice}", f"Late_{metric_choice}"
wf = wl[wl["HasLateWindow"] & (wl["Late_Minutes"] >= min_late) & (wl["Early_Minutes"] >= min_late)].copy()
wf["Change"] = (wf[late_col] - wf[early_col]).round(2)
wf["Player"] = wf["Player"].map(short_name)
wf = wf.sort_values("Change", ascending=False)

if len(wf):
    fig = go.Figure(go.Bar(
        x=wf["Player"], y=wf["Change"],
        marker_color=["#2E7D32" if v > 0 else "#9E2A2B" if v < 0 else CU_SILVER for v in wf["Change"]],
        text=[f"{v:+.1f}" for v in wf["Change"]], textposition="outside",
    ))
    fig.add_hline(y=0, line_dash="dot", line_color="gray")
    fig.update_layout(height=380, margin=dict(t=20), yaxis_title=f"Change in {metric_choice.replace('_per90', '').replace('_', ' ')} per 90 (late minus early)")
    st.plotly_chart(fig, use_container_width=True)
    show = wf[["Player", "PositionGroup", early_col, late_col, "Change", "Early_Minutes", "Late_Minutes"]]
    st.dataframe(pretty_cols(show), use_container_width=True, hide_index=True)
    up, down = wf.head(3), wf.tail(3)
    finding(
        f"Biggest rises: {', '.join(f'{r.Player} ({r.Change:+.1f})' for r in up.itertuples())}. "
        f"Biggest drops: {', '.join(f'{r.Player} ({r.Change:+.1f})' for r in down.itertuples())}.",
        strength="Low", n=f"{len(wf)} players, two 5-match windows",
    )
    st.caption(
        "Each window is five matches, so a change can be a hot or cold stretch, a new opponent mix or a role change as much as a change in form. "
        "The formation also changed between the windows (see the 2026 tab). This shows direction, not steadiness."
    )
else:
    st.info("No players meet the minutes filter. Try lowering it.")

# ---------------------------------------------------------------------------
st.markdown("---")
section_header("2. How steady has each player's role been?")
st.markdown("**Question:** Who plays the same role every match, and who moves between starting and the bench?")

out = rot[rot["Pos"] != "GK"].copy()
g = out.groupby("Player").agg(Matches=("Matches", "sum"), Starts=("Starts", "sum"), SubIn=("SubsIn", "sum"), Minutes=("Minutes", "sum")).reset_index()
g["Min per match played"] = (g["Minutes"] / g["Matches"]).round(0)
g["Started %"] = (g["Starts"] / g["Matches"] * 100).round(0)
g["Share of 10 matches played"] = (g["Matches"] / 10 * 100).round(0)

def role(r):
    if r["Matches"] >= 8 and r["Started %"] >= 80:
        return "Regular starter"
    if r["Matches"] >= 6 and r["Started %"] >= 40:
        return "Rotation starter"
    if r["SubIn"] >= max(1, r["Matches"] // 2):
        return "Mostly off the bench"
    return "Limited minutes"

g["Role"] = g.apply(role, axis=1)
g = g.sort_values(["Starts", "Minutes"], ascending=False)

fig = go.Figure()
fig.add_trace(go.Bar(y=g["Player"], x=g["Starts"], name="Starts", orientation="h", marker_color=CU_NAVY))
fig.add_trace(go.Bar(y=g["Player"], x=g["SubIn"], name="Entered as a substitute", orientation="h", marker_color=CU_LIGHT_BLUE))
fig.update_layout(barmode="stack", height=120 + 26 * len(g), margin=dict(t=10), yaxis=dict(autorange="reversed"),
                  xaxis_title="Matches (out of 10 covered)", legend=dict(orientation="h", y=1.05), legend_title_text="")
st.plotly_chart(fig, use_container_width=True)
tab = g[["Player", "Role", "Matches", "Starts", "SubIn", "Minutes", "Min per match played"]].rename(columns={"SubIn": "Sub appearances", "Minutes": "Total minutes"})
st.dataframe(tab, use_container_width=True, hide_index=True)

nreg = int((g["Role"] == "Regular starter").sum())
finding(
    f"{nreg} outfield players have started at least 80% of the covered matches; "
    f"{int((g['Role'] == 'Mostly off the bench').sum())} come mostly off the bench.",
    strength="Descriptive", n="10 of 13 matches covered",
)
st.caption("Covers the 10 matches in the two windows (not Aug 21, Sep 11 and Sep 13). Roles are simple cutoffs on starts and appearances, not staff designations.")

page_footer()
