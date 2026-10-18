import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from branding import CU_BLUE, CU_NAVY, RESULT_COLORS, page_banner, page_footer, page_nav, finding, short_name

st.set_page_config(page_title="Creighton Bluejays — Development Curves", layout="wide", page_icon="🔵")

page_banner("Development Curves", "Men's Soccer &middot; Typical growth by season in the program")
page_nav("pages/4_Development_Curves.py")
st.markdown("---")

st.markdown(
    "**Question:** What does a typical player's output look like in their 1st, 2nd, 3rd season in the program, "
    "and where do returning players sit on that curve now?"
)
st.caption(
    "Season number counts a player's seasons in the 2021–2025 data, not class year. Someone who arrived before 2021 "
    "may be further along than their number shows. Each point is built from few players, so read the curves as rough shapes."
)

try:
    hist = pd.read_csv("player_season_history.csv")
    current = pd.read_csv("player_stats_2026.csv")
except FileNotFoundError as e:
    st.info(f"Missing file: {e.filename}")
    st.stop()

hist = hist.sort_values(["Player", "Season"]).copy()
hist["SeasonNumber"] = hist.groupby("Player").cumcount() + 1

st.markdown("---")
st.subheader("The Typical Curve, by Position Group")

curve = hist[hist["PositionGroup"].notna()].groupby(["PositionGroup", "SeasonNumber"]).agg(
    n_players=("Player", "nunique"),
    G_per90=("G_per90", "mean"),
    xG_per90=("xG_per90", "mean"),
    Prog_Pass_per90=("Prog Pass_per90", "mean"),
    D_Won_per90=("D Won_per90", "mean"),
).reset_index().round(2)

metric_choice = st.selectbox(
    "Metric to trace", ["G_per90", "xG_per90", "Prog_Pass_per90", "D_Won_per90"],
    format_func=lambda x: {"G_per90": "Goals per 90", "xG_per90": "xG per 90",
                             "Prog_Pass_per90": "Progressive Passes per 90",
                             "D_Won_per90": "Duels Won per 90"}[x],
)

fig = go.Figure()
colors = {"Attackers": "#2E7D32", "Midfielders": CU_BLUE, "Defenders": CU_NAVY}
for group in ["Attackers", "Midfielders", "Defenders"]:
    sub = curve[curve["PositionGroup"] == group]
    fig.add_trace(go.Scatter(
        x=sub["SeasonNumber"], y=sub[metric_choice], mode="lines+markers", name=group,
        line=dict(color=colors[group], width=3),
        text=[f"n={n} players" for n in sub["n_players"]], hoverinfo="text+y",
    ))
fig.update_layout(height=420, margin=dict(t=30), xaxis_title="Season number in program",
                    yaxis_title=metric_choice.replace("_per90", " per 90").replace("_", " "),
                    xaxis=dict(tickmode="linear", dtick=1))
st.plotly_chart(fig, use_container_width=True)
_ns = curve.pivot(index="SeasonNumber", columns="PositionGroup", values="n_players").fillna(0).astype(int)
st.caption("Players behind each point (season number: attackers / midfielders / defenders): "
           + "; ".join(f"{i}: {r.get('Attackers',0)} / {r.get('Midfielders',0)} / {r.get('Defenders',0)}" for i, r in _ns.iterrows())
           + ". Where a count is under about 5, treat that point as a single player's story.")

st.markdown("---")
st.subheader("Where the 2026 roster sits on the curve")

CUR_METRIC_MAP = {"G_per90": "Goals_per90", "xG_per90": "xG_per90",
                    "Prog_Pass_per90": "ProgressivePasses_per90", "D_Won_per90": "DuelsWon_per90"}
METRIC_LABEL = {"G_per90": "Goals", "xG_per90": "xG", "Prog_Pass_per90": "Progressive passes", "D_Won_per90": "Duels won"}


def _key(n):
    parts = str(n).split(" (")[0].split()
    return (parts[0][0], parts[-1])


hist["_k"] = hist["Player"].map(_key)
rows = []
for _, cr in current.iterrows():
    k = _key(cr["Player"])
    ph = hist[hist["_k"] == k].sort_values("Season")
    cur_group = cr["PositionGroup"]
    seasons_in_data = ph["Season"].nunique()
    season_num = seasons_in_data + 1
    hist_group = ph.iloc[-1]["PositionGroup"] if seasons_in_data else None
    exp = curve[(curve["PositionGroup"] == cur_group) & (curve["SeasonNumber"] == season_num)][metric_choice]
    expected = float(exp.iloc[0]) if len(exp) else None
    actual = float(cr[CUR_METRIC_MAP[metric_choice]])
    rows.append({
        "Player": short_name(cr["Player"]),
        "Status": f"Returner, season {season_num}" if seasons_in_data else "New to the data (season 1)",
        "Earlier role": hist_group if hist_group else "—",
        "2026 role": cur_group + (" (changed)" if hist_group and hist_group != cur_group else ""),
        "2026 minutes": int(cr["Minutes"]),
        f"Typical {METRIC_LABEL[metric_choice]}/90 for this role and season": round(expected, 2) if expected is not None else None,
        f"Actual 2026 {METRIC_LABEL[metric_choice]}/90": round(actual, 2),
        "Small sample": "Yes (<90 min)" if cr["Minutes"] < 90 else "",
    })
tbl = pd.DataFrame(rows)
n_ret = int(tbl["Status"].str.startswith("Returner").sum())
n_changed = int(tbl["2026 role"].str.contains("changed").sum())
finding(
    f"{n_ret} of {len(tbl)} outfield players with 2026 minutes have earlier Creighton history in the data; {len(tbl) - n_ret} are new. "
    f"{n_changed} of the returners are listed in a more advanced position than before.",
    strength="Descriptive", n=f"{len(tbl)} players",
)
st.dataframe(tbl.sort_values(["Status", "Player"]), use_container_width=True, hide_index=True)
st.caption(
    "Typical values come from the curve above for the player's 2026 position at the same season number, so they rest on few players. "
    "A role change can move the numbers more than development does. Position labels come from Wyscout and can differ from how the staff describes the role. "
    "New players have no earlier season here; if they transferred in, their season number is understated."
)

page_footer()
