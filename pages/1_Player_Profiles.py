import streamlit as st
import pandas as pd
import plotly.express as px
from branding import CU_BLUE, CU_NAVY, page_banner, page_footer
 
st.set_page_config(page_title="Creighton Bluejays — Player Profiles", layout="wide", page_icon="🔵")
 
page_banner("Player Profiles — Current Roster (2026)", "Men's Soccer &middot; Individual Player Analysis")
 
st.markdown(
    "**Question:** Within each position group, who's producing at a rate above "
    "their peers right now — the first step toward spotting a player on a "
    "breakout trajectory, the way Duncan McGuire's numbers might have looked "
    "before his 2022 run."
)
st.warning(
    "Two honest limits on this whole page: (1) this is only 5 matches into 2026 — "
    "rates from a handful of games can swing a lot, especially for players with "
    "under ~90 minutes played. (2) This report has no data on Duncan McGuire "
    "himself, so nothing here is a literal comparison to his numbers — it's "
    "identifying who's outperforming their CURRENT position group, which is a "
    "related but different claim. Use the minutes filter below to avoid reading "
    "too much into small samples.",
    icon="⚠️",
)
 
try:
    players_df = pd.read_csv("player_stats_2026.csv")
except FileNotFoundError:
    st.info("Add player_stats_2026.csv to this folder to see player profiles.")
    st.stop()
 
min_minutes = st.slider("Minimum minutes played (filters out small samples)", 0, 300, 90, step=15)
filtered_players = players_df[players_df["Minutes"] >= min_minutes].copy()
position_group = st.selectbox("Position group", ["Attackers", "Midfielders", "Defenders"])
group_df = filtered_players[filtered_players["PositionGroup"] == position_group].copy()
 
tab1, tab2, tab3, tab4 = st.tabs([
    "Per-90 Leaders", "Efficiency vs. Volume", "Discipline & Duel Aggression", "Passing Risk/Reward",
])
 
# ---------------------------------------------------------------------------
# TAB 1: Per-90 leaders (the original view)
# ---------------------------------------------------------------------------
with tab1:
    if position_group == "Attackers":
        display_cols = ["Player", "Minutes", "Goals_per90", "xG_per90", "Assists_per90",
                          "ShotAssists_per90", "KeyPasses_per90", "Dribbles_per90"]
    elif position_group == "Midfielders":
        display_cols = ["Player", "Minutes", "KeyPasses_per90", "ProgressivePasses_per90",
                          "PassesToFinalThird_per90", "DuelsWon_per90", "Assists_per90"]
    else:
        display_cols = ["Player", "Minutes", "DefensiveDuelsWon_per90", "AerialDuelsWon_per90",
                          "Interceptions_per90", "RecoveriesOppHalf_per90", "LossesOwnHalf_per90"]
 
    st.markdown(f"**{position_group} — Per-90 Rates (filtered to {min_minutes}+ minutes)**")
    if len(group_df) > 0:
        st.dataframe(
            group_df[display_cols].sort_values(display_cols[2], ascending=False).round(2),
            use_container_width=True, hide_index=True,
        )
    else:
        st.info(f"No {position_group.lower()} meet the {min_minutes}-minute filter — try lowering it.")
 
# ---------------------------------------------------------------------------
# TAB 2: Efficiency vs. Volume — is output coming from doing more, or from
# doing the same amount more effectively?
# ---------------------------------------------------------------------------
with tab2:
    st.markdown("**Is their output coming from doing MORE, or doing it BETTER?**")
    if position_group == "Attackers":
        x_col, y_col = "xG_per90", "Goals_per90"
        x_label, y_label = "Chances Created (xG per 90)", "Goals Scored (per 90)"
        note = (
            "Above the diagonal = converting chances at a rate better than their quality "
            "suggests (hot streak or a real finishing edge — 5 games isn't enough to know which). "
            "Below it = generating good chances but not yet converting them. Far right AND above "
            "the line is the best combination: high volume of good chances, converting them too."
        )
    elif position_group == "Midfielders":
        x_col, y_col = "ProgressivePasses_per90", "KeyPasses_per90"
        x_label, y_label = "Progressive Passes (volume, per 90)", "Key Passes (chance creation, per 90)"
        note = (
            "Far right = moves the ball forward a lot. High up = directly creates chances a lot. "
            "The most valuable profile is both at once — someone who's only far right without being "
            "high up is progressing the ball into areas that aren't leading to shots yet."
        )
    else:
        x_col, y_col = "DefensiveDuels_per90", "DefensiveDuelsWon_per90"
        x_label, y_label = "Defensive Duels Attempted (volume, per 90)", "Defensive Duels Won (per 90)"
        note = (
            "Above the diagonal = winning duels at a high rate relative to how many they attempt "
            "(efficient defender). Far right without being high up = engaging in a lot of duels "
            "but not winning a proportional share — busy, not necessarily effective."
        )
 
    if len(group_df) > 0 and x_col in group_df.columns and y_col in group_df.columns:
        fig = px.scatter(
            group_df, x=x_col, y=y_col, text="Player", size="Minutes",
            color_discrete_sequence=[CU_BLUE], labels={x_col: x_label, y_col: y_label},
        )
        fig.update_traces(textposition="top center")
        fig.update_layout(height=480, margin=dict(t=30))
        st.plotly_chart(fig, use_container_width=True)
        st.caption(note)
    else:
        st.info("Not enough data for this view with the current filters.")
 
# ---------------------------------------------------------------------------
# TAB 3: Discipline & Duel Aggression — does committing fouls come with
# actually winning the duels, or is it just recklessness?
# ---------------------------------------------------------------------------
with tab3:
    st.markdown("**Are fouls the cost of being an effective, aggressive defender — or just recklessness?**")
    st.caption(
        "This compares how often a player commits a foul against how often they actually "
        "win their defensive duels. A player high on fouls AND high on duel-win rate is "
        "playing aggressive and it's working. High fouls with a LOW win rate is a different "
        "conversation — that's giving away free kicks without the payoff."
    )
    duel_pct_col = None
    if "DefensiveDuels" in group_df.columns and "DefensiveDuelsWon" in group_df.columns:
        group_df["DefensiveDuelWinPct"] = (group_df["DefensiveDuelsWon"] / group_df["DefensiveDuels"] * 100).round(1)
        duel_pct_col = "DefensiveDuelWinPct"
 
    if len(group_df) > 0 and duel_pct_col and "FoulsCommitted_per90" in group_df.columns:
        fig = px.scatter(
            group_df, x="FoulsCommitted_per90", y=duel_pct_col, text="Player", size="Minutes",
            color_discrete_sequence=[CU_NAVY],
            labels={"FoulsCommitted_per90": "Fouls Committed (per 90)", duel_pct_col: "Defensive Duel Win %"},
        )
        fig.update_traces(textposition="top center")
        fig.update_layout(height=480, margin=dict(t=30))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough data for this view with the current filters.")
 
# ---------------------------------------------------------------------------
# TAB 4: Passing Risk/Reward — volume of forward-progressing passes vs.
# how often those riskier passes are actually completed.
# ---------------------------------------------------------------------------
with tab4:
    st.markdown("**Playing it safe vs. taking risks: progressive pass volume vs. accuracy**")
    st.caption(
        "Progressive passes (moving the ball meaningfully toward goal) are inherently riskier "
        "than a sideways or backward pass. This shows who's attempting a lot of them (volume) "
        "against how often those attempts actually connect (accuracy) — a way to separate a "
        "player who plays it safe from one who takes on risk, and whether that risk is paying off."
    )
    pass_df = filtered_players.copy()
    if "ProgressivePasses" in pass_df.columns and "ProgressivePassesAccurate" in pass_df.columns:
        pass_df = pass_df[pass_df["ProgressivePasses"] > 0]
        pass_df["ProgressivePassAccuracy"] = (pass_df["ProgressivePassesAccurate"] / pass_df["ProgressivePasses"] * 100).round(1)
        fig = px.scatter(
            pass_df, x="ProgressivePasses_per90", y="ProgressivePassAccuracy", text="Player",
            size="Minutes", color="PositionGroup",
            labels={"ProgressivePasses_per90": "Progressive Passes Attempted (per 90)",
                    "ProgressivePassAccuracy": "Progressive Pass Accuracy (%)"},
        )
        fig.update_traces(textposition="top center")
        fig.update_layout(height=500, margin=dict(t=30))
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "This view intentionally shows all position groups together — passing risk profile "
            "is a team-wide question, not just a midfielder one. Far right = high volume; "
            "high up = those attempts are actually completing."
        )
    else:
        st.info("Progressive passing data not available.")
 
page_footer()
 
