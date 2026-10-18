import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from branding import CU_BLUE, CU_NAVY, CU_LIGHT_BLUE, page_banner, page_footer, page_nav, finding

st.set_page_config(page_title="Creighton Bluejays — Duncan Blueprint", layout="wide", page_icon="🔵")

page_banner("Duncan Blueprint", "Men's Soccer &middot; Duncan McGuire's 2021 and 2022 seasons as a reference for current attackers")
page_nav("pages/2_Duncan_Blueprint.py")
st.markdown("---")

st.markdown(
    "**Question:** Duncan McGuire went from a limited role in 2021 to 23 goals and an Elite Eight run in 2022. "
    "What did his numbers look like before and during the breakout, and which current attackers resemble them?"
)
st.caption("Based on one player's two seasons, so use it to start conversations about who to watch, not to predict outcomes.")

try:
    hist = pd.read_csv("player_season_history.csv")
    current = pd.read_csv("player_stats_2026.csv")
except FileNotFoundError as e:
    st.info(f"Missing file: {e.filename}")
    st.stop()

duncan = hist[hist["Player"].str.contains("McGuire", case=False, na=False)].set_index("Season")
if duncan.empty:
    st.error("Couldn't find Duncan McGuire in player_season_history.csv.")
    st.stop()

METRIC_MAP = {
    "Goals": ("Goals_per90", "G_per90"),
    "xG": ("xG_per90", "xG_per90"),
    "Shots": ("Shots_per90", "Sh_per90"),
    "Duels Won": ("DuelsWon_per90", "D Won_per90"),
    "Progressive Passes": ("ProgressivePasses_per90", "Prog Pass_per90"),
    "Box Touches": ("TouchesPenArea_per90", "Box Touch_per90"),
    "Dribbles": ("Dribbles_per90", "Drib_per90"),
    "Key Passes": ("KeyPasses_per90", "KP_per90"),
}

st.markdown("---")
st.subheader("Duncan McGuire's Actual Trajectory (per 90 minutes)")
duncan_table = pd.DataFrame({
    "2021 (limited role)": [round(duncan.loc[2021, h], 2) for _, h in METRIC_MAP.values()],
    "2022 (breakout)": [round(duncan.loc[2022, h], 2) for _, h in METRIC_MAP.values()],
}, index=list(METRIC_MAP.keys()))
duncan_table["Change"] = (duncan_table["2022 (breakout)"] - duncan_table["2021 (limited role)"]).round(2)
duncan_table.index.name = "Per 90 minutes"
st.dataframe(duncan_table, use_container_width=True)
_p = lambda k: (duncan_table.loc[k, "2022 (breakout)"] / duncan_table.loc[k, "2021 (limited role)"] - 1) * 100
finding(
    f"The jump was in shooting and finishing, not in general involvement: shots per 90 {_p('Shots'):+.0f}%, box touches {_p('Box Touches'):+.0f}%, "
    f"goals per 90 from {duncan_table.loc['Goals','2021 (limited role)']:.2f} to {duncan_table.loc['Goals','2022 (breakout)']:.2f}.",
    strength="Descriptive", n="one player, two seasons",
)
st.caption(
    f"Duels won ({duncan_table.loc['Duels Won','Change']:+.2f}) and progressive passes ({duncan_table.loc['Progressive Passes','Change']:+.2f}) per 90 barely moved or fell. "
    "Goals and xG are rates on a small 2021 base, so the absolute change is shown instead of a percentage."
)

st.markdown("---")
st.subheader("The Real Leading Indicator: What Showed Up BEFORE the Goals Did")
st.markdown(
    "Here his **2021 season, before the breakout,** is compared with every other forward-season in the program's 2021–2025 history. "
    "Question: was there an early sign before he started scoring?"
)

forwards_hist = hist[(hist["PositionGroup"] == "Attackers") & (~hist["Player"].str.contains("McGuire", na=False))]

if not forwards_hist.empty:
    LEADING_METRICS = {"Shots": "Sh_per90", "Box Touches": "Box Touch_per90",
                         "Dribbles": "Drib_per90", "Duels Won": "D Won_per90",
                         "Recoveries": "Recov_per90"}
    duncan21 = duncan.loc[2021]
    lead_rows = []
    for label, col in LEADING_METRICS.items():
        peer_avg = forwards_hist[col].mean()
        d_val = duncan21[col]
        pct = (d_val - peer_avg) / peer_avg * 100 if peer_avg else float("nan")
        lead_rows.append({"Metric": label, "Duncan 2021": round(d_val, 2),
                            f"Peer Avg ({len(forwards_hist)} forward-seasons)": round(peer_avg, 2),
                            "Duncan vs. Peer": f"{pct:+.0f}%"})
    st.dataframe(pd.DataFrame(lead_rows), use_container_width=True, hide_index=True)
    _lr = pd.DataFrame(lead_rows).set_index("Metric")
    st.caption(
        f"In 2021 Duncan was above the peer average on shots ({_lr.loc['Shots','Duncan vs. Peer']}) and duels won ({_lr.loc['Duels Won','Duncan vs. Peer']}), "
        f"and below it on box touches ({_lr.loc['Box Touches','Duncan vs. Peer']}) and dribbles ({_lr.loc['Dribbles','Duncan vs. Peer']}). "
        f"With only {len(forwards_hist)} peer seasons and one breakout player, this is a pattern worth watching, not a tested predictor."
    )

    st.markdown("**Which current attackers already show this exact pattern?**")
    peer_shots = forwards_hist["Sh_per90"].mean()
    peer_duels = forwards_hist["D Won_per90"].mean()
    sig_df = current[(current["PositionGroup"] == "Attackers") & (current["Minutes"] >= 90)].copy()
    sig_df["Shots vs. Peer"] = ((sig_df["Shots_per90"] - peer_shots) / peer_shots * 100).round(0)
    sig_df["Duels Won vs. Peer"] = ((sig_df["DuelsWon_per90"] - peer_duels) / peer_duels * 100).round(0)
    sig_df["Shows Duncan's Signature"] = (sig_df["Shots vs. Peer"] > 0) & (sig_df["Duels Won vs. Peer"] > 0)
    display = sig_df[["Player", "Minutes", "Shots vs. Peer", "Duels Won vs. Peer", "Shows Duncan's Signature"]].sort_values("Shots vs. Peer", ascending=False)
    st.dataframe(display, use_container_width=True, hide_index=True)
    _top = display[display["Shows Duncan's Signature"]].head(3)
    if len(_top):
        st.caption(
            "Players above peer average on both shots and duels won: "
            + ", ".join(f"{r['Player']} ({r['Shots vs. Peer']:+.0f}% shots, {int(r['Minutes'])} min)" for _, r in _top.iterrows())
            + f". Duncan's own 2021 shot rate was {_lr.loc['Shots','Duncan vs. Peer']} vs. peers. "
            "Minutes are limited and cover only part of the season, so treat these as early leads."
        )

st.markdown("---")
st.subheader("Who on the Current Roster Profiles Closest to Duncan's 2022 Season?")

max_minutes_available = int(current["Minutes"].max()) if len(current) else 300
min_minutes = st.slider("Minimum minutes played (2026)", 0, max_minutes_available, 90, step=15, key="duncan_min_min")
attackers = current[(current["PositionGroup"] == "Attackers") & (current["Minutes"] >= min_minutes)].copy()

if len(attackers) == 0:
    st.info("No attackers meet this minutes filter — try lowering it.")
else:
    rows = []
    for _, p in attackers.iterrows():
        diffs = []
        for label, (cur_col, hist_col) in METRIC_MAP.items():
            d22 = duncan.loc[2022, hist_col]
            if d22 and d22 != 0 and cur_col in p and pd.notna(p[cur_col]):
                diffs.append(abs(p[cur_col] - d22) / d22 * 100)
        if diffs:
            rows.append({
                "Player": p["Player"], "Minutes": p["Minutes"],
                "Avg. % Difference from Duncan's 2022 Rate": round(sum(diffs) / len(diffs), 1),
            })
    similarity_df = pd.DataFrame(rows).sort_values("Avg. % Difference from Duncan's 2022 Rate")
    st.dataframe(similarity_df, use_container_width=True, hide_index=True)
    st.caption(
        "Lower = more similar to Duncan's 2022 per-90 profile across all 8 metrics above, "
        "weighted equally. This is a simple average, not a machine-learning model — "
        "transparent on purpose so you can explain exactly how the number was built."
    )

    st.markdown("---")
    st.subheader("Compare One Player Directly Against Both of Duncan's Seasons")
    selected_player = st.selectbox("Pick a current attacker", attackers["Player"].tolist())
    player_row = attackers[attackers["Player"] == selected_player].iloc[0]

    fig = go.Figure()
    metrics = list(METRIC_MAP.keys())
    fig.add_trace(go.Bar(name="Duncan 2021 (limited role)", x=metrics,
                          y=[duncan.loc[2021, h] for _, h in METRIC_MAP.values()],
                          marker_color="#B0B7C3"))
    fig.add_trace(go.Bar(name="Duncan 2022 (breakout)", x=metrics,
                          y=[duncan.loc[2022, h] for _, h in METRIC_MAP.values()],
                          marker_color=CU_NAVY))
    games_label = {"Both windows": "10 of 13 matches", "Early window only": "early window, 5 matches"}.get(
        player_row.get("GamesCovered", ""), "partial season"
    )
    fig.add_trace(go.Bar(name=f"{selected_player} (2026, {games_label})", x=metrics,
                          y=[player_row[cur_col] for cur_col, _ in METRIC_MAP.values()],
                          marker_color=CU_BLUE))
    fig.update_layout(barmode="group", height=480, margin=dict(t=30),
                        yaxis_title="Per 90 minutes", legend_title_text="")
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        f"Where {selected_player}'s bars sit closer to the navy (2022) than the "
        "gray (2021) bars is where their current numbers already resemble the "
        "breakout profile. Where they sit beyond either — higher or lower — is "
        "worth a real conversation, not just a stat to note."
    )

st.markdown("---")
st.subheader("2022 Match by Match")
st.markdown("Duncan's goals in each 2022 match, in order. The 23-goal total came in bursts, not a steady climb.")

try:
    match_log = pd.read_csv("player_match_log.csv")
    duncan_matches = match_log[(match_log["Player"] == "Duncan McGuire") & (match_log["Season"] == 2022)].sort_values("Date").reset_index(drop=True)
    duncan_matches["MatchNum"] = range(1, len(duncan_matches) + 1)
    duncan_matches["CumGoals"] = duncan_matches["G"].cumsum()
    duncan_matches["Rolling3_G"] = duncan_matches["G"].rolling(3, min_periods=1).mean().round(2)
    duncan_matches["Rolling3_xG"] = duncan_matches["xG"].rolling(3, min_periods=1).mean().round(2)

    fig_traj = go.Figure()
    fig_traj.add_trace(go.Bar(x=duncan_matches["MatchNum"], y=duncan_matches["G"], name="Goals (that match)", marker_color=CU_LIGHT_BLUE))
    fig_traj.add_trace(go.Scatter(x=duncan_matches["MatchNum"], y=duncan_matches["Rolling3_G"], name="3-Match Rolling Avg (Goals)", mode="lines", line=dict(color=CU_NAVY, width=3)))
    fig_traj.add_trace(go.Scatter(x=duncan_matches["MatchNum"], y=duncan_matches["Rolling3_xG"], name="3-Match Rolling Avg (xG)", mode="lines", line=dict(color=CU_BLUE, width=2, dash="dot")))
    fig_traj.update_layout(height=450, margin=dict(t=30), xaxis_title="Match Number (2022 Season)", yaxis_title="Goals", legend=dict(orientation="h", yanchor="bottom", y=1.02))
    st.plotly_chart(fig_traj, use_container_width=True)

    st.markdown(
        """
**How the season unfolded:**

- **Matches 1-2:** 5 goals combined (3 vs. Oakland, 2 vs. Rutgers) — the hot start everyone remembers.
- **Matches 3-5:** a 3-match scoreless stretch, including a match at Stanford with
  0.00 xG, a game where he barely got a chance.
- **Matches 6-17:** a long grinding middle stretch — a goal every match or two, unspectacular
  but steady, this is where most of the "23 goals" actually accumulated in small pieces.
- **Match 18 (Nov 10, Seton Hall):** his single best match of the season — 4 goals, 2.41 xG —
  bigger than the season opener that gets remembered as the moment it started.
- **Matches 19-24:** a mixed, tapering finish — not every game down the stretch was a big one.

**Why it matters for reading a current player's form:** the breakout season included a
3-match scoreless stretch. A few quiet matches in a row did not mean the season was off track.
        """
    )
except FileNotFoundError:
    st.info("Add player_match_log.csv to this folder to see the match-by-match trajectory.")

page_footer()
