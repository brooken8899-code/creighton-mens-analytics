import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from branding import CU_BLUE, CU_NAVY, CU_LIGHT_BLUE, CU_SILVER, RESULT_COLORS, section_header, page_banner, page_footer, page_nav, finding

st.set_page_config(page_title="Creighton Bluejays — 2022 Beyond Duncan", layout="wide", page_icon="🔵")

page_banner("2022 Beyond Duncan", "Men's Soccer &middot; How Much of 2022 Was the Team, Not the Star")
page_nav("pages/9_2022_Beyond_Duncan.py")
st.markdown("---")

st.markdown(
    "**Question:** Duncan McGuire scored 23 goals in 2022, but the team also got the best "
    "results in this data. How much came from him, and how much from the rest of the team: "
    "its supporting attack, its defense, its style, or how settled the lineup was?"
)

finding(
    "Duncan's scoring mattered, but the rest of the 2022 attack was also the strongest in the data. The defense was ordinary, and the lineup was settled but not uniquely so.",
    strength="Moderate", n="19 matches in 2022, compared with 2023–2025",
)

try:
    m = pd.read_csv("creighton_matches_combined.csv")
    log = pd.read_csv("player_match_log.csv")
    full = pd.read_csv("creighton_full_combined.csv")
except FileNotFoundError as e:
    st.info(f"Missing file: {e.filename}")
    st.stop()

m["Season"] = m["Season"].astype(str)
m["Date"] = pd.to_datetime(m["Date"])
m = m[m["Season"].isin(["2022", "2023", "2024", "2025"])].copy()
log["Date"] = pd.to_datetime(log["Date"])
full["Season"] = full["Season"].astype(str)

# ---- Remove each season's top scorer from that season's team numbers (like for like) ----
star_rows, season_rows = [], []
for s in ["2022", "2023", "2024", "2025"]:
    x = log[log["Season"] == int(s)]
    goals = x.groupby("Player")["G"].sum().sort_values(ascending=False)
    star = goals.index[0]
    sd = x[x["Player"] == star][["Date", "Opponent", "G", "xG"]].copy()
    sd["Opp"] = sd["Opponent"].str[:8]
    tm = m[m["Season"] == s].copy()
    g_, xg_ = [], []
    for _, r in tm.iterrows():
        # same opponent and within 2 days (the two exports date some matches a day apart);
        # take the nearest date so back-to-back opponents can't be mixed up
        c = sd[(sd["Opp"] == r["Opponent"][:8]) & ((sd["Date"] - r["Date"]).abs() <= pd.Timedelta(days=2))]
        c = c.assign(gap=(c["Date"] - r["Date"]).abs()).sort_values("gap")
        g_.append(c["G"].iloc[0] if len(c) else 0)
        xg_.append(c["xG"].iloc[0] if len(c) else 0)
    tm["StarG"], tm["StarxG"] = g_, xg_
    star_rows.append(tm)
    season_rows.append({
        "Season": s, "Top scorer": star, "Matches": len(tm),
        "Goals/match": tm["GoalsFor"].mean(), "Goals/match without top scorer": (tm["GoalsFor"] - tm["StarG"]).mean(),
        "xG/match": tm["xG"].mean(), "xG/match without top scorer": (tm["xG"] - tm["StarxG"]).mean(),
        "Goals against/match": tm["GoalsAgainst"].mean(),
        "Possession %": tm["Possession, %"].mean(), "PPDA": tm["PPDA"].mean(),
        "Win %": (tm["Result"] == "Win").mean() * 100,
    })
seasons = pd.DataFrame(season_rows).set_index("Season")
all_m = pd.concat(star_rows)

# ---------------------------------------------------------------------------
section_header("1. The Attack Without Its Star")
st.markdown("Each season's top scorer's goals and chances are removed from that season's team numbers, so 2022 is compared with the other years like for like.")
c1, c2 = st.columns(2)
for col, (a, b, title) in zip([c1, c2], [
    ("Goals/match", "Goals/match without top scorer", "Goals per match"),
    ("xG/match", "xG/match without top scorer", "Chances created (xG) per match"),
]):
    with col:
        st.markdown(f"**{title}**")
        fig = go.Figure()
        fig.add_trace(go.Bar(x=seasons.index, y=seasons[a], name="Whole team", marker_color=CU_LIGHT_BLUE))
        fig.add_trace(go.Bar(x=seasons.index, y=seasons[b], name="Without top scorer", marker_color=CU_NAVY))
        fig.update_layout(barmode="group", height=360, margin=dict(t=20), legend_title_text="")
        fig.update_xaxes(type='category')
        st.plotly_chart(fig, use_container_width=True)
s22, s25 = seasons.loc["2022"], seasons.drop("2022")
st.caption(
    f"Without Duncan, 2022 still scored {s22['Goals/match without top scorer']:.2f} goals per match "
    f"from {s22['xG/match without top scorer']:.2f} xG. The other seasons without their top scorers "
    f"scored {s25['Goals/match without top scorer'].min():.2f} to {s25['Goals/match without top scorer'].max():.2f}. "
    "The supporting attack was stronger in 2022 than in any other year here. "
    "Duncan's goals cover the matches in the team file; four of his 23 came in postseason games it doesn't include."
)

dm = log[(log["Season"] == 2022) & (log["Player"] == "Duncan McGuire")]
st.caption(
    f"Duncan himself scored 23 goals from {dm['xG'].sum():.1f} xG across all 2022 matches, "
    f"{dm['G'].sum() - dm['xG'].sum():+.1f} above what his chances were worth."
)

st.markdown("**Results when Duncan scored vs. when he didn't (2022)**")
t22 = all_m[all_m["Season"] == "2022"].copy()
t22["Duncan"] = np.where(t22["StarG"] > 0, "Duncan scored", "Duncan didn't score")
rec = t22.groupby("Duncan")["Result"].value_counts().unstack(fill_value=0).reindex(columns=["Win", "Draw", "Loss"], fill_value=0)
rec["Goals/match"] = t22.groupby("Duncan")["GoalsFor"].mean().round(2)
st.dataframe(rec, use_container_width=True)
st.caption(
    "The team's results track Duncan's scoring closely, which is partly built in: when a team scores more, it wins more. "
    "This shows how much the results leaned on him, not that he caused them."
)

st.markdown("---")
# ---------------------------------------------------------------------------
section_header("2. The Defense")
c1, c2 = st.columns(2)
with c1:
    st.markdown("**Goals against per match**")
    fig = px.bar(seasons.reset_index(), x="Season", y="Goals against/match", color_discrete_sequence=[CU_BLUE])
    fig.update_layout(height=340, margin=dict(t=20))
    fig.update_xaxes(type='category')
    st.plotly_chart(fig, use_container_width=True)
with c2:
    st.markdown("**Shots against per match**")
    sa = full.groupby("Season")["ShotsAgainst"].mean().reset_index()
    fig = px.bar(sa, x="Season", y="ShotsAgainst", color_discrete_sequence=[CU_NAVY])
    fig.update_layout(height=340, margin=dict(t=20), yaxis_title="Shots against")
    fig.update_xaxes(type='category')
    st.plotly_chart(fig, use_container_width=True)
best_def = seasons["Goals against/match"].idxmin()
st.caption(
    f"2022 allowed {seasons.loc['2022', 'Goals against/match']:.2f} goals per match. "
    f"The tightest defense in this data was {best_def} ({seasons.loc[best_def, 'Goals against/match']:.2f}). "
    "2022's defense was ordinary, so the data doesn't support 'it was a great defensive team'."
)

st.markdown("---")
# ---------------------------------------------------------------------------
section_header("3. The Style")
f = full.groupby("Season")[["SmartPasses", "PenaltyAreaEntries", "Crosses"]].mean().round(2)
f["Possession %"] = seasons["Possession %"].round(1)
f["PPDA (lower = more pressing)"] = seasons["PPDA"].round(2)
st.dataframe(f, use_container_width=True)
st.caption(
    "2022 had the most possession and the most smart passes of any season (see the Team Dashboard for the full picture), "
    "while pressing intensity looks like the other years. The style was different, and it came with the attack above. "
    "From one season we can't separate style from the players who ran it."
)

st.markdown("---")
# ---------------------------------------------------------------------------
section_header("4. Chemistry: How Settled Was the Lineup?")
rows = []
for s in [2022, 2023, 2024, 2025]:
    x = log[log["Season"] == s]
    starters = x[x["Min"] >= 60].groupby("Date")["Player"].apply(set).sort_index()
    jac = [len(a & b) / len(a | b) for a, b in zip(starters.values[:-1], starters.values[1:])]
    played = x[x["Min"] > 0].groupby("Player")["Min"].sum().sort_values(ascending=False)
    rows.append({"Season": str(s), "Starter overlap match to match": np.mean(jac),
                 "Minutes share of top 11 players": played.head(11).sum() / played.sum()})
chem = pd.DataFrame(rows).set_index("Season")
st.markdown("**Starter overlap: how much of the starting group carried over from one match to the next**")
fig = px.bar(chem.reset_index(), x="Season", y="Starter overlap match to match", color_discrete_sequence=[CU_BLUE])
fig.update_layout(height=340, margin=dict(t=20), yaxis_tickformat=".0%")
fig.update_xaxes(type='category')
st.plotly_chart(fig, use_container_width=True)
st.caption(
    f"2022 had a very settled group ({chem.loc['2022', 'Starter overlap match to match']:.0%} overlap), "
    f"but 2023 was about the same ({chem.loc['2023', 'Starter overlap match to match']:.0%}) and won far fewer matches "
    f"({seasons.loc['2023', 'Win %']:.0f}% vs {seasons.loc['2022', 'Win %']:.0f}%). A stable lineup looks like part of the "
    "story, not the whole of it. This is only a stand-in for chemistry: it measures who played together, "
    "not how well they played together. Starters here are players with 60+ minutes, and the log includes postseason matches."
)

st.markdown("---")
section_header("What the Data Says So Far")
st.markdown(
    """
- **Attack beyond Duncan: supported.** The rest of the 2022 team scored and created more than any other season's team does without its top scorer.
- **Defense: not supported.** 2022 allowed a middling number of goals. 2025 was tighter.
- **Style: supported as a difference.** More possession and more smart passes than any other year, but we can't tell the style from the players.
- **Chemistry: partly.** The lineup was settled, but 2023 was just as settled and did much worse.
- **Duncan's role:** a big one. His 23 goals beat his chances by about 5, and results leaned heavily on whether he scored.

One season can't separate these causes. This page rules explanations in or out; it doesn't rank them.
    """
)

page_footer()
