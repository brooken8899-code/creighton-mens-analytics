import re
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from branding import (CU_BLUE, CU_NAVY, CU_LIGHT_BLUE, CU_SILVER, RESULT_COLORS,
                      section_header, page_banner, page_footer, page_nav, finding)

st.set_page_config(page_title="Creighton Bluejays — Multi-Season Analysis", layout="wide", page_icon="🔵")

# ---------------------------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------------------------
df_all = pd.read_csv("creighton_matches_combined.csv")
df_all["Date"] = pd.to_datetime(df_all["Date"])
df_all["Season"] = df_all["Season"].astype(str)
df_all = df_all.sort_values("Date")
df_all["xG_diff"] = df_all["GoalsFor"] - df_all["xG"]          # goals minus chances created
df_all["xG_net"] = df_all["xG"] - df_all["xGA"]                # chances created minus chances allowed

# ---------------------------------------------------------------------------
# SIDEBAR: season filter
# ---------------------------------------------------------------------------
st.sidebar.title("Filters")
all_seasons = sorted(df_all["Season"].unique())
selected_seasons = st.sidebar.multiselect("Seasons", all_seasons, default=all_seasons)
st.sidebar.caption("Sections 1–3 follow this filter. Section 4 uses 2022–2025 where full match detail exists (possession also includes 2026).")
df = df_all[df_all["Season"].isin(selected_seasons)].copy()
if df.empty:
    st.warning("Select at least one season in the sidebar.")
    st.stop()

# ---------------------------------------------------------------------------
# HEADER
# ---------------------------------------------------------------------------
page_banner("Creighton Men's Soccer — Team Analysis", "Wyscout team-match data, 2022–2026")
page_nav("app.py")
st.markdown("---")

c1, c2, c3, c4, c5 = st.columns([1.5, 0.8, 1.2, 1.2, 1.3])
c1.metric("Record", f"{(df['Result']=='Win').sum()}W-{(df['Result']=='Draw').sum()}D-{(df['Result']=='Loss').sum()}L")
c2.metric("Matches", len(df))
c3.metric("Goals for / against", f"{int(df['GoalsFor'].sum())} / {int(df['GoalsAgainst'].sum())}")
c4.metric("xG for / against", f"{df['xG'].sum():.0f} / {df['xGA'].sum():.0f}")
c5.metric("Avg. xG margin / match", f"{df['xG_net'].mean():+.2f}")
st.caption(f"Showing: {', '.join(selected_seasons)}. xG (expected goals) is the quality of the chances a team creates; xG against is the quality of the chances it allows.")

# ---------------------------------------------------------------------------
# KEY FINDINGS (always computed on every season, independent of the sidebar filter)
# ---------------------------------------------------------------------------
section_header("Key Findings")
s26 = df_all[df_all["Season"] == "2026"]
by_season_net = df_all.groupby("Season")["xG_net"].mean()
hist_net = df_all[df_all["Season"] != "2026"]
d22 = pd.read_csv("creighton_differentials.csv")
d22_res = d22.groupby("Result")[["xG_Creighton", "xG_Opp", "Goals_Creighton", "Goals_Opp"]].mean()
n_loss = int((d22["Result"] == "Loss").sum())
full_k = pd.read_csv("creighton_full_combined.csv")
poss = full_k[full_k["Result"].isin(["Win", "Loss"])].groupby("Result")["Possession_pct"].mean()
smart = full_k.groupby("Season")["SmartPasses"].mean()
smart_top = smart.idxmax()

if len(s26):
    w, d_, l = (s26["Result"] == "Win").sum(), (s26["Result"] == "Draw").sum(), (s26["Result"] == "Loss").sum()
    finding(
        f"2026 is {w}W-{d_}D-{l}L and the underlying numbers back it up: {s26['xG'].mean():.2f} xG created vs. "
        f"{s26['xGA'].mean():.2f} allowed per match ({by_season_net['2026']:+.2f} margin, the best of any season here).",
        strength="Moderate", n=f"{len(s26)} matches",
    )
    over = s26["GoalsFor"].mean() - s26["xG"].mean()
    st.caption(
        f"Goals are running {over:+.2f} per match above chance quality, so part of the scoring is finishing that may not hold. "
        f"The chance margin is the steadier signal."
    )
finding(
    f"In 2022–25 losses, Creighton created slightly more than it allowed ({d22_res.loc['Loss','xG_Creighton']:.2f} vs. "
    f"{d22_res.loc['Loss','xG_Opp']:.2f} xG) but scored {d22_res.loc['Loss','xG_Creighton']-d22_res.loc['Loss','Goals_Creighton']:.1f} fewer than its xG and "
    f"conceded {d22_res.loc['Loss','Goals_Opp']-d22_res.loc['Loss','xG_Opp']:.1f} more than the opponent's.",
    strength="Moderate; partly built in", n=f"{n_loss} losses",
)
finding(
    f"Possession was higher in losses ({poss['Loss']:.0f}%) than in wins ({poss['Win']:.0f}%) in 2022–25. "
    "Teams that trail tend to keep the ball, so read it as game state, not as a reason to hold the ball less.",
    strength="Suggestive", n=f"{int((full_k['Result']=='Loss').sum())} losses, {int((full_k['Result']=='Win').sum())} wins",
)
finding(
    f"{smart_top} had the most smart passes per match ({smart.max():.1f}, vs. {smart.drop(smart_top).max():.1f} in the next-highest season), "
    "but one season can't tell us whether the style produced the results.",
    strength="Descriptive", n="one season",
)
st.markdown("---")

# ---------------------------------------------------------------------------
# SECTION 1: CHANCES CREATED vs. CHANCES ALLOWED
# ---------------------------------------------------------------------------
section_header("1. Chances vs. Results")
st.markdown("**Question:** When Creighton loses, is it because the opponent created more, or because results went against the chances?")

res_tbl = df.groupby("Result").agg(
    Matches=("xG", "size"), xG_for=("xG", "mean"), xG_against=("xGA", "mean"),
    Goals_for=("GoalsFor", "mean"), Goals_against=("GoalsAgainst", "mean"),
).round(2).reindex(["Win", "Draw", "Loss"]).dropna(how="all")
res_tbl.columns = ["Matches", "xG for", "xG against", "Goals for", "Goals against"]

c1, c2 = st.columns([1, 1])
with c1:
    st.markdown("**Average per match, by result**")
    st.dataframe(res_tbl, use_container_width=True)
    lo = res_tbl.loc["Loss"] if "Loss" in res_tbl.index else None
    if lo is not None:
        finding(
            f"In losses Creighton created {lo['xG for']:.2f} xG and allowed {lo['xG against']:.2f}, "
            f"but scored {lo['Goals for']:.2f} and conceded {lo['Goals against']:.2f}.",
            strength="Moderate", n=f"{int(lo['Matches'])} losses in selection",
        )
    st.caption(
        "A loss will always look like 'scored less than expected' because that is part of what a loss is, "
        "so this table shows the size of the swing, not its cause. Whether it repeats (finishing, goalkeeping, or luck) "
        "needs more matches than one season provides."
    )
with c2:
    st.markdown("**Each match: chances created vs. goals scored**")
    fig1 = px.scatter(
        df, x="xG", y="GoalsFor", color="Result", color_discrete_map=RESULT_COLORS,
        category_orders={"Result": ["Win", "Draw", "Loss"]},
        hover_data={"Opponent": True, "Date": "|%b %d, %Y", "xG": ":.2f"},
        labels={"xG": "xG (chances created)", "GoalsFor": "Goals scored"},
    )
    mx = float(max(df["xG"].max(), df["GoalsFor"].max())) + 0.5
    fig1.add_trace(go.Scatter(x=[0, mx], y=[0, mx], mode="lines", line=dict(color=CU_SILVER, dash="dot"), name="Goals = xG", hoverinfo="skip"))
    fig1.update_traces(marker=dict(size=9, opacity=0.8), selector=dict(mode="markers"))
    fig1.update_layout(height=380, margin=dict(t=20), legend_title_text="")
    st.plotly_chart(fig1, use_container_width=True)
    st.caption("Above the dotted line = scored more than the chances suggested; below = fewer.")

st.subheader("Chances created and allowed, by season")
net = df.groupby("Season").agg(xG_for=("xG", "mean"), xG_against=("xGA", "mean"), n=("xG", "size")).reset_index()
fig1b = go.Figure()
fig1b.add_trace(go.Bar(x=net["Season"], y=net["xG_for"], name="xG created", marker_color=CU_NAVY))
fig1b.add_trace(go.Bar(x=net["Season"], y=net["xG_against"], name="xG allowed", marker_color=CU_LIGHT_BLUE))
fig1b.update_layout(barmode="group", height=340, margin=dict(t=20), yaxis_title="Per match", xaxis=dict(type="category"), legend_title_text="")
st.plotly_chart(fig1b, use_container_width=True)
st.caption("Matches per season: " + ", ".join(f"{r.Season}: {r.n}" for r in net.itertuples()) + ". The 2026 season is still in progress.")

st.markdown("---")

# ---------------------------------------------------------------------------
# SECTION 2: HOME / AWAY SPLIT
# ---------------------------------------------------------------------------
section_header("2. Home vs. Away")
st.markdown("**Question:** Does location change how Creighton performs?")

c1, c2 = st.columns(2)
with c1:
    home_away = df.groupby("HomeAway").agg(
        Matches=("xG", "size"), xG_for=("xG", "mean"), xG_against=("xGA", "mean"),
        Goals_for=("GoalsFor", "mean"), Goals_against=("GoalsAgainst", "mean"),
    ).round(2)
    home_away.columns = ["Matches", "xG for", "xG against", "Goals for", "Goals against"]
    st.dataframe(home_away, use_container_width=True)
    if {"Home", "Away"} <= set(home_away.index):
        gap = home_away.loc["Home", "Goals for"] - home_away.loc["Away", "Goals for"] - (home_away.loc["Home", "Goals against"] - home_away.loc["Away", "Goals against"])
        gd = df.assign(GD=df["GoalsFor"] - df["GoalsAgainst"]).groupby(["Season", "HomeAway"])["GD"].mean().unstack()
        per_season = (gd["Home"] - gd["Away"]).dropna()
        finding(
            f"Home matches net {gap:+.2f} more goals than away matches across the selection.",
            strength="Modest", n=f"{len(df)} matches",
        )
        st.caption(
            "Home minus away goal difference, by season: "
            + ", ".join(f"{s} {v:+.1f}" for s, v in per_season.items())
            + ". The gap changes size from year to year, so one season can mislead on its own."
        )
with c2:
    st.markdown("**Results by location**")
    results_by_location = df.groupby(["HomeAway", "Result"]).size().reset_index(name="Matches")
    fig2 = px.bar(
        results_by_location, x="HomeAway", y="Matches", color="Result", barmode="stack",
        category_orders={"Result": ["Win", "Draw", "Loss"], "HomeAway": ["Home", "Away"]},
        color_discrete_map=RESULT_COLORS, labels={"HomeAway": "Location"},
    )
    fig2.update_layout(margin=dict(t=20), height=320, legend_title_text="")
    fig2.update_xaxes(type='category')
st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# ---------------------------------------------------------------------------
# SECTION 3: PPDA (PRESSING INTENSITY)
# ---------------------------------------------------------------------------
section_header("3. Pressing Intensity (PPDA)")
st.markdown(
    "**Question:** Does pressing intensity line up with results? "
    "PPDA counts opponent passes per defensive action in the opponent's final 60% of the pitch; lower means more aggressive pressing."
)

if "PPDA" in df.columns and df["PPDA"].notna().any():
    c1, c2 = st.columns([1, 2])
    with c1:
        ppda_summary = df.groupby("Result")["PPDA"].agg(["mean", "std", "count"]).round(2).reindex(["Win", "Draw", "Loss"]).dropna(how="all")
        ppda_summary.columns = ["Average PPDA", "Spread (std. dev.)", "Matches"]
        st.dataframe(ppda_summary, use_container_width=True)
        finding("PPDA is nearly the same in wins, draws and losses.", strength="Clear: no pattern", n=f"{int(ppda_summary['Matches'].sum())} matches")
        st.caption("Averages are close and the spread is much larger than the gaps between them. Pressing intensity is not a result predictor in this data.")
    with c2:
        st.markdown("**PPDA by match, with a 5-match rolling average**")
        d3 = df.dropna(subset=["PPDA"]).sort_values("Date").copy()
        d3["Match #"] = d3.groupby("Season").cumcount() + 1
        d3["5-match average"] = d3.groupby("Season")["PPDA"].transform(lambda x: x.rolling(5, min_periods=3).mean())
        fig3 = px.scatter(
            d3, x="Match #", y="PPDA", color="Result", facet_col="Season", color_discrete_map=RESULT_COLORS,
            category_orders={"Result": ["Win", "Draw", "Loss"]}, hover_data=["Opponent"],
        )
        seasons = list(d3["Season"].unique())
        for i, s_ in enumerate(seasons, start=1):
            g_ = d3[d3["Season"] == s_]
            fig3.add_trace(go.Scatter(x=g_["Match #"], y=g_["5-match average"], mode="lines", line=dict(color=CU_NAVY, width=2),
                                      name="5-match average", showlegend=(i == 1), hoverinfo="skip"), row=1, col=i)
        fig3.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        fig3.update_xaxes(title_text="", dtick=5)
        fig3.add_annotation(text="Match number within season", xref="paper", yref="paper", x=0.5, y=-0.16, showarrow=False)
        fig3.update_layout(margin=dict(t=30, b=50), height=360, legend_title_text="", yaxis_title="PPDA (lower = more pressing)")
        st.plotly_chart(fig3, use_container_width=True)
else:
    st.info("PPDA not available in this dataset.")

st.markdown("---")

# ---------------------------------------------------------------------------
# SECTION 4: THE 2022 BLUEPRINT & HIDDEN FACTORS
# ---------------------------------------------------------------------------
section_header("4. What Separates Wins from Losses (2022–2026)")
st.markdown(
    "**Question:** Which match habits differ between Creighton's wins and losses, "
    "and what stood out about the 2022 Elite Eight season?"
)

try:
    df_full = pd.read_csv("creighton_full_combined.csv")
    df_full["Season"] = df_full["Season"].astype(str)

    st.subheader("Possession was higher in losses than in wins, in every season")
    _pm = df_all.copy()
    _pm["Season"] = _pm["Season"].astype(str)
    _pm = _pm[_pm["Season"] != "2021"]
    poss_by_season = _pm[_pm["Result"].isin(["Win", "Loss"])].groupby(["Season", "Result"])["Possession, %"].mean().reset_index()
    fig4 = px.bar(
        poss_by_season, x="Season", y="Possession, %", color="Result", barmode="group",
        category_orders={"Result": ["Win", "Loss"]},
        color_discrete_map=RESULT_COLORS,
        labels={"Possession, %": "Possession %"},
    )
    fig4.update_layout(margin=dict(t=30))
    fig4.update_xaxes(type='category')
    st.plotly_chart(fig4, use_container_width=True)
    _pc = _pm[_pm["Result"].isin(["Win", "Loss"])].groupby(["Season", "Result"]).size().unstack().fillna(0)
    st.caption(
        "Creighton averaged more possession in losses than in wins in each of 2022–2025 "
        f"(matches per season, wins/losses: " + ", ".join(f"{i}: {int(r['Win'])}/{int(r['Loss'])}" for i, r in _pc.iterrows()) + "). "
        "2026 is included, but with no losses so far (10W-3D-0L) it has only a win bar. "
        f"The same pattern shows up against draws: 2026 wins averaged {_pm[(_pm['Season']=='2026') & (_pm['Result']=='Win')]['Possession, %'].mean():.0f}% possession and draws {_pm[(_pm['Season']=='2026') & (_pm['Result']=='Draw')]['Possession, %'].mean():.0f}% (10 wins, 3 draws). "
        "Possession by itself says little: teams that are behind keep the ball more, and teams that lead sit back, "
        "so this likely reflects how games unfolded rather than a flaw in holding the ball."
    )

    st.subheader("Match habits in wins vs. losses")
    st.caption(
        "Per-match averages. The 2023–25 columns are the baseline; 2022 is shown separately "
        "so that season doesn't blur the comparison. 2026 is not in this table: the 2026 team export doesn't include these columns "
        "(crosses, attacking duels, box entries, smart passes), and there are no 2026 losses to compare against."
    )
    key_metrics = ["OffensiveDuels", "Crosses", "PenaltyAreaEntries_Crosses",
                   "PositionalAttacks_withShots_pct", "Fouls", "Losses_High"]
    METRIC_LABELS = {
        "OffensiveDuels": "Individual 1v1 Attacking Duels (per game)",
        "Crosses": "Crosses Attempted (per game)",
        "PenaltyAreaEntries_Crosses": "Box Entries via Cross (per game)",
        "PositionalAttacks_withShots_pct": "Build-Up Possessions Ending in a Shot (%)",
        "Fouls": "Fouls Committed (per game)",
        "Losses_High": "Turnovers in the Attacking Third (per game)",
    }
    current_era = df_full[df_full["Season"] != "2022"]
    blueprint_2022 = df_full[df_full["Season"] == "2022"]

    win_loss = current_era[current_era["Result"].isin(["Win", "Loss"])].groupby("Result")[key_metrics].mean().round(2).T
    win_loss.columns = ["Loss Avg (2023–25)", "Win Avg (2023–25)"]
    # Split 2022 by result too, the same way the current era is split — a single
    # blended 2022 number would mix wins, draws, and losses together, which isn't
    # a fair comparison against columns that ARE split by result.
    blueprint_win_loss = blueprint_2022[blueprint_2022["Result"].isin(["Win", "Loss"])].groupby("Result")[key_metrics].mean().round(2)
    win_loss["2022 Loss Avg"] = blueprint_win_loss.loc["Loss"] if "Loss" in blueprint_win_loss.index else float("nan")
    win_loss["2022 Win Avg"] = blueprint_win_loss.loc["Win"] if "Win" in blueprint_win_loss.index else float("nan")
    win_loss.index = [METRIC_LABELS[m] for m in win_loss.index]
    _n = current_era[current_era["Result"].isin(["Win", "Loss"])]["Result"].value_counts()
    _n22 = blueprint_2022[blueprint_2022["Result"].isin(["Win", "Loss"])]["Result"].value_counts()
    st.dataframe(win_loss.round(1), use_container_width=True)
    st.caption(
        f"Based on {_n.get('Win', 0)} wins and {_n.get('Loss', 0)} losses in 2023–25, and {_n22.get('Win', 0)} wins and {_n22.get('Loss', 0)} losses in 2022. "
        "Losses involve more individual 1v1 attacking duels and more crosses, while wins turn a larger share of build-up possessions into a shot. "
        "These are descriptions of how games went, not tested causes: teams chasing a game also take more crosses and duels."
    )

    st.subheader("Smart passes per match, by season")
    smart_by_season = df_full.groupby("Season")[["SmartPasses", "SmartPassesAccurate"]].mean().round(2).reset_index()
    fig5 = px.bar(
        smart_by_season, x="Season", y=["SmartPasses", "SmartPassesAccurate"], barmode="group",
        labels={"value": "Smart Passes per Game", "variable": "Metric"},
        color_discrete_sequence=[CU_LIGHT_BLUE, CU_NAVY],
    )
    fig5.update_layout(margin=dict(t=30))
    fig5.update_xaxes(type='category')
    st.plotly_chart(fig5, use_container_width=True)
    _sp = smart_by_season.set_index("Season")["SmartPasses"]
    st.caption(
        f"Smart passes are attempts to break the defense, such as through balls. 2022 averaged {_sp['2022']:.1f} per match, "
        f"{_sp['2022']/_sp.drop('2022').max():.1f}x the next-highest season ({_sp.drop('2022').idxmax()}, {_sp.drop('2022').max():.1f}). "
        "It describes how that team played; it doesn't show the style caused the results. "
        "2026 is not shown because the 2026 team file has no smart pass column; it will be added once the full 2026 export is loaded."
    )

except FileNotFoundError:
    st.info("Add creighton_full_combined.csv to this folder to see this section.")


page_footer()
