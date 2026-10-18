from math import exp, factorial

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from branding import (CU_BLUE, CU_NAVY, CU_LIGHT_BLUE, CU_SILVER, RESULT_COLORS,
                      section_header, page_banner, page_footer, page_nav, finding, short_name)

st.set_page_config(page_title="Creighton Bluejays — 2026 Under the Surface", layout="wide", page_icon="🔵")

page_banner("2026 Under the Surface", "Men's Soccer &middot; What this season's 13 matches show beyond the record")
page_nav("pages/11_2026_Under_the_Surface.py")
st.markdown("---")

try:
    m = pd.read_csv("creighton_matches_combined.csv")
    cur = pd.read_csv("player_stats_2026.csv")
    hist = pd.read_csv("player_season_history.csv")
    rot = pd.read_csv("rotation_2026.csv")
except FileNotFoundError as e:
    st.info(f"Missing file: {e.filename}")
    st.stop()

m["Season"] = m["Season"].astype(str)
m["Date"] = pd.to_datetime(m["Date"])
m = m.sort_values("Date")
m["Points"] = m["Result"].map({"Win": 3, "Draw": 1, "Loss": 0})


def _pois(lam, k):
    return exp(-lam) * lam ** k / factorial(k)


def expected_points(xg_for, xg_against, cap=12):
    """Expected points from the two xG values, treating each team's goals as independent Poisson counts."""
    w = d = 0.0
    for i in range(cap):
        for j in range(cap):
            p = _pois(xg_for, i) * _pois(xg_against, j)
            if i > j:
                w += p
            elif i == j:
                d += p
    return 3 * w + d


m["xP"] = [expected_points(a, b) for a, b in zip(m["xG"], m["xGA"])]
s26 = m[m["Season"] == "2026"].copy()
s26["Match"] = range(1, len(s26) + 1)
per_season = m.groupby("Season").agg(Matches=("Points", "size"), Points=("Points", "sum"), xP=("xP", "sum")).reset_index()
per_season["Gap"] = per_season["Points"] - per_season["xP"]
g26 = per_season[per_season["Season"] == "2026"].iloc[0]

# ---------------------------------------------------------------------------
# Summary computed from the data below
# ---------------------------------------------------------------------------
section_header("Summary")
finding(
    f"Results are ahead of the performances: {int(g26['Points'])} points from {int(g26['Matches'])} matches, where the chances created and allowed "
    f"point to about {g26['xP']:.0f} ({g26['Gap']:+.1f}). That is the largest gap of any season in the data.",
    strength="Moderate", n=f"{int(g26['Matches'])} matches",
)
sum_box = st.container()

# ---------------------------------------------------------------------------
# 1. Results vs. chances
# ---------------------------------------------------------------------------
st.markdown("---")
section_header("1. Are the results ahead of the performances?")
st.markdown(
    "**Question:** Given the chances Creighton created and allowed in each match, how many points would a typical team have earned, "
    "and how does that compare with the points actually won?"
)

c1, c2 = st.columns([3, 2])
with c1:
    s26["Cumulative points"] = s26["Points"].cumsum()
    s26["Cumulative expected points"] = s26["xP"].cumsum()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=s26["Match"], y=s26["Cumulative points"], mode="lines+markers", name="Actual points",
                             line=dict(color=CU_NAVY, width=3), text=s26["Opponent"], hovertemplate="%{text}<br>Actual: %{y}<extra></extra>"))
    fig.add_trace(go.Scatter(x=s26["Match"], y=s26["Cumulative expected points"], mode="lines+markers", name="Expected points (from xG)",
                             line=dict(color=CU_LIGHT_BLUE, width=3, dash="dot"), text=s26["Opponent"], hovertemplate="%{text}<br>Expected: %{y:.1f}<extra></extra>"))
    fig.update_layout(height=360, margin=dict(t=20), xaxis_title="Match number, 2026", yaxis_title="Cumulative points",
                      xaxis=dict(tickmode="linear", dtick=1), legend_title_text="", legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)
with c2:
    ps = per_season.copy()
    fig = go.Figure(go.Bar(
        x=ps["Season"], y=ps["Gap"],
        marker_color=[CU_NAVY if s == "2026" else CU_LIGHT_BLUE for s in ps["Season"]],
        text=[f"{v:+.1f}" for v in ps["Gap"]], textposition="outside",
    ))
    fig.add_hline(y=0, line_dash="dot", line_color="gray")
    fig.update_layout(height=360, margin=dict(t=20), yaxis_title="Points minus expected points", xaxis=dict(type="category"))
    st.plotly_chart(fig, use_container_width=True)
st.caption(
    "Left: 2026 points won vs. points expected from each match's xG for and against. Right: the same gap for every season. "
    "Expected points treat each side's goals as random draws around its xG, so they describe what the chances were worth, not what should have happened in any one match."
)

tbl = s26[["Match", "Date", "Opponent", "Result", "GoalsFor", "GoalsAgainst", "xG", "xGA", "Points", "xP"]].copy()
tbl["Date"] = tbl["Date"].dt.strftime("%b %d")
tbl["Points vs. expected"] = (tbl["Points"] - tbl["xP"]).round(2)
tbl = tbl.rename(columns={"GoalsFor": "GF", "GoalsAgainst": "GA", "xG": "xG for", "xGA": "xG against", "xP": "Expected pts"})
tbl[["xG for", "xG against", "Expected pts"]] = tbl[["xG for", "xG against", "Expected pts"]].round(2)
with st.expander("Match-by-match table"):
    st.dataframe(tbl.sort_values("Points vs. expected", ascending=False), use_container_width=True, hide_index=True)

top_lucky = tbl.sort_values("Points vs. expected", ascending=False).head(3)
top_unlucky = tbl.sort_values("Points vs. expected").head(2)
st.markdown(
    "**Where the gap comes from:** "
    + "; ".join(f"{r['Opponent']} ({r['GF']:.0f}-{r['GA']:.0f}, {r['xG for']:.1f} xG to {r['xG against']:.1f}, {r['Points vs. expected']:+.1f} pts)" for _, r in top_lucky.iterrows())
    + ". Fewer points than the chances suggested: "
    + "; ".join(f"{r['Opponent']} ({r['GF']:.0f}-{r['GA']:.0f}, {r['Points vs. expected']:+.1f} pts)" for _, r in top_unlucky.iterrows()) + "."
)
finding(
    f"The team's underlying margin is the best in the data ({s26['xG'].mean() - s26['xGA'].mean():+.2f} xG per match), so the record is not an illusion. "
    "But a few narrow results carried part of it, so the margin for error is thinner than the record suggests.",
    strength="Moderate", n="13 matches",
)

# ---------------------------------------------------------------------------
# 2. Who contributes beyond goals?
# ---------------------------------------------------------------------------
st.markdown("---")
section_header("2. Who contributes beyond goals?")
st.markdown(
    "**Question:** Which players do a lot of the work that doesn't show up in goals and assists, "
    "compared with how Creighton players in the same position group have done in past seasons?"
)

METRICS = {
    "Progressive passes": ("ProgressivePasses_per90", "Prog Pass_per90"),
    "Key passes": ("KeyPasses_per90", "KP_per90"),
    "Dribbles": ("Dribbles_per90", "Drib_per90"),
    "Duels won": ("DuelsWon_per90", "D Won_per90"),
    "Aerial duels won": ("AerialDuelsWon_per90", "Air Won_per90"),
    "Interceptions": ("Interceptions_per90", "Int_per90"),
}
c1, c2 = st.columns(2)
with c1:
    group = st.selectbox("Position group", ["Midfielders", "Defenders", "Attackers"], key="surf_group")
with c2:
    min_min = st.slider("Minimum 2026 minutes", 0, 600, 150, step=30, key="surf_min")

bench = hist[(hist["PositionGroup"] == group) & (hist["Min"] >= 450)]
players = cur[(cur["PositionGroup"] == group) & (cur["Minutes"] >= min_min)].copy()
usable = {k: v for k, v in METRICS.items() if v[0] in players.columns and v[1] in bench.columns and bench[v[1]].notna().sum() >= 5}

if players.empty or len(bench) < 5:
    st.info("Not enough players at this filter. Try lowering the minimum minutes.")
else:
    pct = pd.DataFrame(index=players["Player"].map(short_name))
    for label, (cc, hc) in usable.items():
        ref = bench[hc].dropna().values
        pct[label] = [round((ref < v).mean() * 100) for v in players[cc].values]
    pct["Minutes"] = players["Minutes"].values
    pct = pct.sort_values("Minutes", ascending=False)
    z = pct.drop(columns="Minutes")
    fig = px.imshow(
        z.values, x=list(z.columns), y=list(z.index), text_auto=True, aspect="auto",
        color_continuous_scale=["#F2F4F7", CU_LIGHT_BLUE, CU_NAVY], zmin=0, zmax=100,
        labels=dict(color="Percentile"),
    )
    fig.update_xaxes(side="top")
    fig.update_layout(height=120 + 38 * len(z), margin=dict(t=60, b=10), coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        f"Each cell is the player's 2026 per-90 rate as a percentile of the {len(bench)} {group.lower()[:-1]} seasons from 2021–2025 with 450+ minutes "
        "(50 = typical, 90 = higher than 90% of them). Players are listed by 2026 minutes, most first. "
        "Duel and interception rates come from the early window only; the others cover both windows."
    )

    MIN_STAND = 300
    stand, thin = [], []
    for name, row in z.iterrows():
        hi = [f"{c} ({int(v)})" for c, v in row.items() if v >= 80]
        if not hi:
            continue
        mins = int(pct.loc[name, "Minutes"])
        (stand if mins >= MIN_STAND else thin).append({"Player": name, "2026 minutes": mins, "80th percentile or higher": ", ".join(hi)})
    if stand:
        st.markdown(f"**Standouts ({MIN_STAND}+ minutes)**")
        st.dataframe(pd.DataFrame(stand), use_container_width=True, hide_index=True)
    else:
        st.caption(f"No player with {MIN_STAND}+ minutes in this group reaches the 80th percentile on any of these measures.")
    if thin:
        st.caption(
            "Too few minutes to call standouts (a handful of actions can swing these rates): "
            + ", ".join(f"{t['Player']} ({t['2026 minutes']} min)" for t in thin) + "."
        )
    st.caption(
        "These measures count how much a player does, not how well. High numbers can reflect a role (a midfielder asked to defend a lot) as much as quality, "
        "so use them to ask questions, not to rank players. Defensive duels are left out because the 2026 report's counts are about twice the 2021–25 scale, so the comparison wouldn't be fair."
    )

# ---------------------------------------------------------------------------
# 3. Formation
# ---------------------------------------------------------------------------
st.markdown("---")
section_header("3. Has the shape changed, and did the numbers change with it?")
st.markdown("**Question:** Creighton's main formation moved during the season. How did performance compare across shapes?")

s26["Shape"] = np.where(s26["Scheme"].isin(["5-3-2", "3-5-2"]), "5-3-2 / 3-5-2", "3-4-3 / 3-4-2-1")
shape = s26.groupby("Shape").agg(
    Matches=("Points", "size"), Wins=("Result", lambda r: (r == "Win").sum()), Draws=("Result", lambda r: (r == "Draw").sum()),
    Losses=("Result", lambda r: (r == "Loss").sum()), GF=("GoalsFor", "mean"), GA=("GoalsAgainst", "mean"),
    xG=("xG", "mean"), xGA=("xGA", "mean"), Poss=("Possession, %", "mean"), PPDA=("PPDA", "mean"),
).round(2)
shape["Record"] = shape["Wins"].astype(str) + "-" + shape["Draws"].astype(str) + "-" + shape["Losses"].astype(str)
shape["xG margin"] = (shape["xG"] - shape["xGA"]).round(2)
shape = shape[["Matches", "Record", "GF", "GA", "xG", "xGA", "xG margin", "Poss", "PPDA"]]
shape.columns = ["Matches", "W-D-L", "Goals for", "Goals against", "xG for", "xG against", "xG margin", "Possession %", "PPDA"]
st.dataframe(shape, use_container_width=True)

fig = go.Figure()
sc = {"3-4-3 / 3-4-2-1": CU_LIGHT_BLUE, "5-3-2 / 3-5-2": CU_NAVY}
fig.add_trace(go.Bar(x=s26["Match"], y=s26["xG"], name="xG for", marker_color=[sc[x] for x in s26["Shape"]],
                     text=s26["Scheme"], textposition="outside", hovertext=s26["Opponent"]))
fig.add_trace(go.Scatter(x=s26["Match"], y=s26["xGA"], mode="lines+markers", name="xG against", line=dict(color=CU_SILVER, width=2), hovertext=s26["Opponent"]))
fig.update_layout(height=360, margin=dict(t=20), xaxis_title="Match number, 2026", yaxis_title="xG", xaxis=dict(tickmode="linear", dtick=1),
                  legend=dict(orientation="h", y=1.1), legend_title_text="", showlegend=True)
st.plotly_chart(fig, use_container_width=True)
st.caption("Bar color shows the shape (light = 3-4-3 / 3-4-2-1, navy = 5-3-2 / 3-5-2); the label is the formation used for most of the match.")

a, b = s26[s26["Shape"] == "3-4-3 / 3-4-2-1"], s26[s26["Shape"] == "5-3-2 / 3-5-2"]
if len(a) and len(b):
    finding(
        f"Since the move to a back five ({len(b)} matches), Creighton creates {b['xG'].mean():.2f} xG per match instead of {a['xG'].mean():.2f}, "
        f"and allows {b['xGA'].mean():.2f} instead of {a['xGA'].mean():.2f}. The record is {int((b['Result']=='Win').sum())}W-{int((b['Result']=='Draw').sum())}D-{int((b['Result']=='Loss').sum())}L, "
        f"with {b['GoalsFor'].mean():.2f} goals per match against {a['GoalsFor'].mean():.2f} before.",
        strength="Low", n=f"{len(b)} matches vs. {len(a)}",
    )
    big_east_b = int((b["Competition"] == "Big East").sum()); big_east_a = int((a["Competition"] == "Big East").sum())
    st.caption(
        f"Caution: the back-five matches include {big_east_b} Big East games of {len(b)}, against {big_east_a} of {len(a)} in the earlier shape, so opposition and "
        "schedule changed at the same time as the formation. Four matches can't separate the two."
    )

hist_back = m[(m["Season"] != "2026") & (m["Scheme"].isin(["5-3-2", "5-4-1", "3-5-2"]))]
if len(hist_back):
    st.caption(
        f"For reference, in 2022–25 Creighton used a back five in {len(hist_back)} matches, with {hist_back['xG'].mean():.2f} xG for and {hist_back['xGA'].mean():.2f} against on average. "
        "Those were often reactive choices against specific opponents."
    )

# ---------------------------------------------------------------------------
# 4. Rotation
# ---------------------------------------------------------------------------
st.markdown("---")
section_header("4. How settled is the lineup?")
st.markdown("**Question:** Who starts, who comes off the bench, and did the starting group settle as the season went on?")

rot["Short"] = rot["Player"]
wins = list(rot["Window"].unique())
early_w = [w for w in wins if w.startswith("Early")][0]
late_w = [w for w in wins if w.startswith("Late")][0]
out = rot[rot["Pos"] != "GK"]
pv = out.pivot_table(index="Player", columns="Window", values=["Starts", "Minutes", "Matches"], aggfunc="sum").fillna(0)
rows = []
for p in pv.index:
    rows.append({
        "Player": p,
        "Early starts": int(pv.loc[p, ("Starts", early_w)]), "Early matches": int(pv.loc[p, ("Matches", early_w)]), "Early minutes": int(pv.loc[p, ("Minutes", early_w)]),
        "Late starts": int(pv.loc[p, ("Starts", late_w)]), "Late matches": int(pv.loc[p, ("Matches", late_w)]), "Late minutes": int(pv.loc[p, ("Minutes", late_w)]),
    })
rt = pd.DataFrame(rows)
rt["Change in minutes"] = rt["Late minutes"] - rt["Early minutes"]
rt = rt.sort_values("Late minutes", ascending=False)

def core(col, n=4):
    return int((rt[col] >= n).sum())

all_early = out[out["Window"] == early_w]["Minutes"].sort_values(ascending=False)
all_late = out[out["Window"] == late_w]["Minutes"].sort_values(ascending=False)
sh_e = all_early.head(10).sum() / all_early.sum()
sh_l = all_late.head(10).sum() / all_late.sum()
finding(
    f"Minutes are more concentrated in a core group: the top 10 outfield players hold {sh_l:.0%} of outfield minutes in the late window vs. {sh_e:.0%} in the early one. "
    f"{core('Late starts')} outfield players started 4 or more of the last 5 matches (early window: {core('Early starts')}).",
    strength="Descriptive", n="two 5-match windows",
)

melt = rt.melt(id_vars="Player", value_vars=["Early minutes", "Late minutes"], var_name="Window", value_name="Minutes")
fig = px.bar(melt, x="Minutes", y="Player", color="Window", orientation="h", barmode="group",
             color_discrete_map={"Early minutes": CU_LIGHT_BLUE, "Late minutes": CU_NAVY})
fig.update_layout(height=120 + 28 * len(rt), margin=dict(t=10), legend_title_text="", yaxis=dict(autorange="reversed"),
                  xaxis_title="Outfield minutes in the window (5 matches = 450 max)")
st.plotly_chart(fig, use_container_width=True)
st.caption(
    "Early window: Aug 23 – Sep 8. Late window: Sep 19 – Oct 3. The Aug 21, Sep 11 and Sep 13 matches are not covered. "
    "Starts are matches played minus matches entered as a substitute."
)

rising = rt[rt["Change in minutes"] >= 100].head(4)
falling = rt[rt["Change in minutes"] <= -100].sort_values("Change in minutes").head(4)
if len(rising) or len(falling):
    st.markdown(
        ("**More minutes in the late window:** " + ", ".join(f"{r['Player']} ({r['Change in minutes']:+d})" for _, r in rising.iterrows()) + ". " if len(rising) else "")
        + ("**Fewer:** " + ", ".join(f"{r['Player']} ({r['Change in minutes']:+d})" for _, r in falling.iterrows()) + "." if len(falling) else "")
    )
with st.expander("Starts and minutes by player"):
    st.dataframe(rt, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# 5. Team trend
# ---------------------------------------------------------------------------
st.markdown("---")
section_header("5. Is the team's process getting better or worse?")
st.markdown("**Question:** Setting aside results, did the chances created and allowed move in either direction across the 13 matches?")

s26["xG margin"] = s26["xG"] - s26["xGA"]
s26["Rolling 3-match margin"] = s26["xG margin"].rolling(3, min_periods=3).mean()
fig = go.Figure()
fig.add_trace(go.Bar(x=s26["Match"], y=s26["xG margin"], name="Match xG margin", marker_color=CU_LIGHT_BLUE, hovertext=s26["Opponent"]))
fig.add_trace(go.Scatter(x=s26["Match"], y=s26["Rolling 3-match margin"], mode="lines", name="3-match average", line=dict(color=CU_NAVY, width=3)))
fig.add_hline(y=0, line_dash="dot", line_color="gray")
fig.update_layout(height=340, margin=dict(t=20), xaxis_title="Match number, 2026", yaxis_title="xG for minus xG against",
                  xaxis=dict(tickmode="linear", dtick=1), legend=dict(orientation="h", y=1.1), legend_title_text="")
st.plotly_chart(fig, use_container_width=True)

first, last = s26.iloc[:6], s26.iloc[6:]
trend = pd.DataFrame({
    "First 6 matches": [first["xG"].mean(), first["xGA"].mean(), first["xG margin"].mean(), first["Possession, %"].mean(), first["PPDA"].mean(), first["GoalsFor"].mean(), first["GoalsAgainst"].mean()],
    "Last 7 matches": [last["xG"].mean(), last["xGA"].mean(), last["xG margin"].mean(), last["Possession, %"].mean(), last["PPDA"].mean(), last["GoalsFor"].mean(), last["GoalsAgainst"].mean()],
}, index=["xG for", "xG against", "xG margin", "Possession %", "PPDA (lower = more pressing)", "Goals for", "Goals against"]).round(2)
trend["Change"] = (trend["Last 7 matches"] - trend["First 6 matches"]).round(2)
st.dataframe(trend, use_container_width=True)
finding(
    f"Chance creation fell from {first['xG'].mean():.2f} to {last['xG'].mean():.2f} xG per match between the first six matches and the last seven, "
    f"while chances allowed went from {first['xGA'].mean():.2f} to {last['xGA'].mean():.2f}. The margin moved from {first['xG margin'].mean():+.2f} to {last['xG margin'].mean():+.2f}.",
    strength="Low to moderate", n="6 vs. 7 matches; schedule changed (Big East play began)",
)
st.caption(
    "The later matches include Big East opponents, which are generally stronger than early non-conference opponents. "
    "Part of the change is opposition, and part may be the formation change in Section 3."
)

# summary bullets, filled after the numbers exist
with sum_box:
    st.markdown(
        f"""
- **Chances created and allowed are the best of any season** ({s26['xG'].mean():.2f} vs. {s26['xGA'].mean():.2f} xG per match), but points are {g26['Gap']:+.1f} ahead of what they predict.
- **Chance creation has fallen** from {first['xG'].mean():.2f} to {last['xG'].mean():.2f} xG per match since the opening six matches, as the shape moved to a back five and Big East play began.
- **The starting group has settled** (Section 4), and Section 2 shows who does a lot of the non-scoring work among regular players.
        """
    )

page_footer()
