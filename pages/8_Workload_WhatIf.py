import os
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from branding import CU_BLUE, CU_NAVY, CU_LIGHT_BLUE, page_banner, page_footer, page_nav

st.set_page_config(page_title="Creighton Bluejays — Workload What-If", layout="wide", page_icon="🔵")

page_banner("Workload What-If", "Men's Soccer &middot; 2026 Roster, with Duncan McGuire's 2022 as a Benchmark")
page_nav("pages/8_Workload_WhatIf.py")
st.markdown("---")

# A real export takes priority; otherwise fall back to the simulated sample.
load_file = "catapult_matches.csv" if os.path.exists("catapult_matches.csv") else "catapult_sample.csv"
try:
    cat = pd.read_csv(load_file)
    cur = pd.read_csv("player_stats_2026.csv")
    log = pd.read_csv("player_match_log.csv")
except FileNotFoundError as e:
    st.info(f"Missing file: {e.filename}")
    st.stop()

simulated = "Source" in cat.columns and (cat["Source"] == "SIMULATED").any()
if simulated:
    st.error(
        "**ILLUSTRATIVE DATA — NOT CREIGHTON'S GPS DATA.** The workload numbers on this page are "
        "simulated. Minutes and match output (goals, shots, passes, duels) are real Wyscout data. "
        "Nothing here describes a real player's physical load, and the patterns are not findings. "
        "This shows what the analysis would look like once a real Catapult export is added.",
        icon="⚠️",
    )

# Real output, per player-season: 2026 roster from the merged roster file,
# Duncan McGuire's 2022 from the match log. Same four metrics for both.
out26 = cur.rename(columns={"Minutes": "Min", "DuelsWon": "DuelsWon"})[
    ["Player", "Min", "Goals", "Shots", "Passes", "DuelsWon"]].copy()
out26["Season"] = 2026
d = log[(log["Player"] == "Duncan McGuire") & (log["Season"] == 2022)]
duncan = pd.DataFrame([{"Player": "Duncan McGuire", "Season": 2022, "Min": d["Min"].sum(),
                        "Goals": d["G"].sum(), "Shots": d["Shots"].sum(),
                        "Passes": d["Passes"].sum(), "DuelsWon": d["Duels Won"].sum()}])
out = pd.concat([out26, duncan], ignore_index=True)

df = out.merge(cat.drop(columns=[c for c in ["Min", "Source"] if c in cat.columns]),
               on=["Player", "Season"], how="inner")
df["Label"] = np.where(df["Season"] == 2022, df["Player"] + " (2022)", df["Player"])
df["Group"] = np.where(df["Season"] == 2022, "Duncan McGuire, 2022 benchmark", "2026 roster")
for c in ["Goals", "Shots", "Passes", "DuelsWon", "HighSpeedDist_m", "SprintDist_m", "PlayerLoad"]:
    df[f"{c}_p90"] = df[c] / df["Min"] * 90

st.markdown(
    "**The idea:** match stats say what a player produced. GPS data says what it cost him. "
    "Side by side, a coach can ask how much output a player keeps as load builds, and what "
    "changes if his minutes change."
)
st.caption(
    "2026 rates cover each player's available games (10 of 13 matches for most; see Player "
    "Profiles for who has gaps). Duncan's 2022 line is his full real season: 23 goals in 1,798 minutes."
)

tab1, tab2 = st.tabs(["Load vs. Output", "Minutes What-If"])

with tab1:
    st.markdown("**Does higher physical load go with more output?**")
    output_choice = st.selectbox(
        "Output metric", ["DuelsWon_p90", "Shots_p90", "Passes_p90", "Goals_p90"],
        format_func=lambda x: {"DuelsWon_p90": "Duels won per 90", "Shots_p90": "Shots per 90",
                               "Passes_p90": "Passes per 90", "Goals_p90": "Goals per 90"}[x],
    )
    load_choice = st.selectbox(
        "Load metric", ["HighSpeedDist_m_p90", "SprintDist_m_p90", "PlayerLoad_p90"],
        format_func=lambda x: {"HighSpeedDist_m_p90": "High-speed running (m per 90)",
                               "SprintDist_m_p90": "Sprint distance (m per 90)",
                               "PlayerLoad_p90": "Player load per 90"}[x],
    )
    min_minutes = st.slider("Minimum minutes played", 0, 600, 150, step=30)
    plot_df = df[df["Min"] >= min_minutes]
    if len(plot_df) >= 3:
        fig = px.scatter(plot_df, x=load_choice, y=output_choice, text="Label", size="Min", color="Group",
                         color_discrete_map={"2026 roster": CU_BLUE, "Duncan McGuire, 2022 benchmark": CU_NAVY})
        fig.update_traces(textposition="top center")
        fig.update_layout(height=500, margin=dict(t=30), legend_title_text="",
                          xaxis_title="Load (per 90)", yaxis_title="Output (per 90)")
        st.plotly_chart(fig, use_container_width=True)
        roster = plot_df[plot_df["Season"] == 2026]
        if simulated:
            st.caption(
                "Load values are simulated, so no correlation is shown. With a real Catapult export, look for players well above the pack on output "
                "for the same load (efficient) and players who run a lot for little output. Duncan's dot shows where a 23-goal season sat against today's group."
            )
        else:
            r = roster[load_choice].corr(roster[output_choice])
            st.caption(
                f"Correlation across {len(roster)} players on the 2026 roster: {r:.2f}. Look for players well above the pack on output for the same load "
                "(efficient) and players who run a lot for little output. Duncan's dot shows where a 23-goal season sat against today's group."
            )
    else:
        st.info("Not enough players at this minutes filter.")

with tab2:
    st.markdown("**What happens to a player's total output if his minutes change?**")
    choices = df.sort_values(["Season", "Label"], ascending=[False, True])["Label"].tolist()
    if not choices:
        st.info("No players available.")
    else:
        label = st.selectbox("Player", choices)
        p = df[df["Label"] == label].iloc[0]
        c1, c2 = st.columns(2)
        with c1:
            target_min = st.slider("Minutes in a match", 20, 100, 90, step=5)
        with c2:
            fade = st.slider("Assumed fade after 60 min (output lost by minute 90)", 0, 30, 10,
                             format="%d%%") / 100
        metric = st.selectbox("Output", ["Duels won", "Shots", "Passes", "Goals"])
        key = {"Duels won": "DuelsWon", "Shots": "Shots", "Passes": "Passes", "Goals": "Goals"}[metric]
        rate90 = p[f"{key}_p90"]
        m = np.arange(0, target_min + 1)
        flat = rate90 / 90 * m
        faded = np.cumsum(rate90 / 90 * np.where(m > 60, 1 - fade * (m - 60) / 30, 1.0))
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=m, y=flat, name="Constant rate", line=dict(color=CU_LIGHT_BLUE, dash="dot")))
        fig.add_trace(go.Scatter(x=m, y=faded, name=f"With {int(fade*100)}% fade", line=dict(color=CU_NAVY, width=3)))
        fig.update_layout(height=420, margin=dict(t=30), xaxis_title="Minutes played",
                          yaxis_title=f"Cumulative {metric.lower()}", legend_title_text="")
        st.plotly_chart(fig, use_container_width=True)
        k1, k2, k3 = st.columns(3)
        k1.metric(f"Projected {metric.lower()}", f"{faded[-1]:.2f}")
        k2.metric("Projected player load", f"{p['PlayerLoad'] / p['Min'] * target_min:.0f}" + (" (sim.)" if simulated else ""))
        k3.metric("Minutes in sample", int(p["Min"]))
        st.caption(
            f"Rate = {label}'s real output per 90 ({rate90:.2f}). The fade is an assumption you set, "
            "not something estimated from data. Small minute totals make rates swing, so treat "
            "players under about 150 minutes with caution. With real GPS data the fade could be "
            "fitted from how output changes late in matches and after high-load weeks."
        )

page_footer()
