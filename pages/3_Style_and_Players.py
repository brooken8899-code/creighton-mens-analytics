import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from branding import (CU_BLUE, CU_NAVY, CU_LIGHT_BLUE, CU_SILVER, RESULT_COLORS,
                      page_banner, page_footer, page_nav, section_header, finding, short_name)

st.set_page_config(page_title="Creighton Bluejays — Style & Players", layout="wide", page_icon="🔵")

page_banner("Style & Players", "Men's Soccer &middot; How the 2026 team plays, and who carries the passing")
page_nav("pages/3_Style_and_Players.py")
st.markdown("---")

try:
    m = pd.read_csv("creighton_matches_combined.csv")
    cur = pd.read_csv("player_stats_2026.csv")
    ev = pd.read_csv("player_2026_early_vs_late.csv")
except FileNotFoundError as e:
    st.info(f"Missing file: {e.filename}")
    st.stop()

m["Season"] = m["Season"].astype(str)
m["Date"] = pd.to_datetime(m["Date"])
s26 = m[m["Season"] == "2026"].sort_values("Date").reset_index(drop=True)
s26["Match"] = s26.index + 1
prior = m[m["Season"] != "2026"]

# ---------------------------------------------------------------------------
section_header("1. How the team has played in 2026")
st.markdown("**Question:** How much of the ball does Creighton have, and how hard does it press, match to match?")
c1, c2 = st.columns(2)
with c1:
    fig = px.bar(s26, x="Match", y="Possession, %", color="Result", color_discrete_map=RESULT_COLORS, hover_data=["Opponent", "Scheme"])
    fig.add_hline(y=50, line_dash="dot", line_color="gray")
    fig.update_layout(height=320, margin=dict(t=20), yaxis_title="Possession %", xaxis=dict(tickmode="linear", dtick=1), legend_title_text="")
    st.plotly_chart(fig, use_container_width=True)
with c2:
    fig = px.bar(s26, x="Match", y="PPDA", color="Result", color_discrete_map=RESULT_COLORS, hover_data=["Opponent", "Scheme"])
    fig.update_layout(height=320, margin=dict(t=20), yaxis_title="PPDA (lower = more pressing)", xaxis=dict(tickmode="linear", dtick=1), legend_title_text="")
    st.plotly_chart(fig, use_container_width=True)
st.caption("Possession is Creighton's share of the ball. PPDA is the opponent's passes allowed per defensive action in the opponent's final 60% of the pitch, so a lower number means more aggressive pressing.")

finding(
    f"2026 averages {s26['Possession, %'].mean():.0f}% possession and a PPDA of {s26['PPDA'].mean():.1f}, "
    f"compared with {prior['Possession, %'].mean():.0f}% and {prior['PPDA'].mean():.1f} across 2022–25.",
    strength="Descriptive", n="13 matches in 2026",
)

# ---------------------------------------------------------------------------
st.markdown("---")
section_header("2. Who carries the passing")
st.markdown("**Question:** Which players handle the most passes, and who moves the ball forward?")

min_min = st.slider("Minimum 2026 minutes", 0, 600, 150, step=30, key="style_min")
p = cur[cur["Minutes"] >= min_min].copy()
p["Name"] = p["Player"].map(short_name)
p["Passes/90"] = p["Passes"] / p["Minutes"] * 90
p["Pass accuracy %"] = p["PassesAccurate"] / p["Passes"] * 100
p["Forward pass share %"] = p["ForwardPasses"] / p["Passes"] * 100
p["Progressive/90"] = p["ProgressivePasses_per90"]
p["Key passes/90"] = p["KeyPasses_per90"]
p["Share of team passes %"] = p["Passes"] / cur["Passes"].sum() * 100

if p.empty:
    st.info("No players at this minimum. Lower the slider.")
else:
    fig = px.scatter(
        p, x="Passes/90", y="Progressive/90", size="Minutes", color="PositionGroup", text="Name",
        color_discrete_map={"Defenders": CU_NAVY, "Midfielders": CU_LIGHT_BLUE, "Attackers": CU_SILVER},
        hover_data={"Minutes": True, "Passes/90": ":.1f", "Progressive/90": ":.1f"},
    )
    fig.update_traces(textposition="top center")
    fig.update_layout(height=470, margin=dict(t=20), legend_title_text="", xaxis_title="Passes per 90", yaxis_title="Progressive passes per 90")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Bubble size shows 2026 minutes. Players further right handle more of the ball; players higher up play more passes that move it significantly toward goal.")

    tab = p.sort_values("Passes/90", ascending=False)[["Name", "PositionGroup", "Minutes", "Passes/90", "Pass accuracy %", "Forward pass share %", "Progressive/90", "Key passes/90", "Share of team passes %"]]
    tab = tab.rename(columns={"Name": "Player", "PositionGroup": "Position"}).round(1)
    st.dataframe(tab, use_container_width=True, hide_index=True)

    top = tab.head(3)
    finding(
        "Most passing volume per 90: " + ", ".join(f"{r['Player']} ({r['Passes/90']:.0f})" for _, r in top.iterrows()) + ".",
        strength="Descriptive", n=f"{len(p)} players",
    )

# ---------------------------------------------------------------------------
st.markdown("---")
section_header("3. Did passing change from the early to the late window?")
st.markdown("**Question:** Between the early window (Aug 23 – Sep 8) and the late window (Sep 19 – Oct 3), who passes more or less per 90?")

e = ev[ev["HasLateWindow"] == True].copy()
e = e[(e["Early_Minutes"] >= 90) & (e["Late_Minutes"] >= 90)]
e["Change"] = e["Late_Passes_per90"] - e["Early_Passes_per90"]
e = e.sort_values("Change")
if len(e):
    fig = go.Figure(go.Bar(
        x=e["Change"], y=e["Player"], orientation="h",
        marker_color=[CU_NAVY if v >= 0 else CU_LIGHT_BLUE for v in e["Change"]],
        text=[f"{v:+.1f}" for v in e["Change"]], textposition="outside",
    ))
    fig.add_vline(x=0, line_dash="dot", line_color="gray")
    fig.update_layout(height=120 + 30 * len(e), margin=dict(t=10), xaxis_title="Change in passes per 90 (late minus early)")
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"Players with at least 90 minutes in both windows ({len(e)} players). Each window is five matches, so individual changes are noisy.")

early_m, late_m = s26.iloc[1:6], s26.iloc[8:13]
finding(
    f"Team possession was {early_m['Possession, %'].mean():.0f}% in the early window and {late_m['Possession, %'].mean():.0f}% in the late window; "
    f"PPDA moved from {early_m['PPDA'].mean():.1f} to {late_m['PPDA'].mean():.1f}. "
    "The formation also changed in this period (see the 2026 tab), so changes in player passing reflect role and opponent as well as style.",
    strength="Low", n="two 5-match windows",
)

page_footer()
