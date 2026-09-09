import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from branding import CU_BLUE, CU_NAVY, CU_LIGHT_BLUE, CU_SILVER, RESULT_COLORS, section_header, page_banner, page_footer

st.set_page_config(page_title="Creighton Bluejays — Multi-Season Analysis", layout="wide", page_icon="🔵")

# ---------------------------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------------------------
df_all = pd.read_csv("creighton_matches_combined.csv")
df_all["Date"] = pd.to_datetime(df_all["Date"])
df_all["Season"] = df_all["Season"].astype(str)
df_all = df_all.sort_values("Date")

# ---------------------------------------------------------------------------
# SIDEBAR: season filter
# ---------------------------------------------------------------------------
st.sidebar.title("Filters")
all_seasons = sorted(df_all["Season"].unique())
selected_seasons = st.sidebar.multiselect("Seasons", all_seasons, default=all_seasons)
df = df_all[df_all["Season"].isin(selected_seasons)].copy()

# ---------------------------------------------------------------------------
# HEADER
# ---------------------------------------------------------------------------
# To show the official Bluejay logo: download it from Creighton Athletics'
# brand assets (gocreighton.com) and save it as "logo.png" in this same
# folder. This code will pick it up automatically. Skipped quietly if not found.
page_banner("Creighton Bluejays — Multi-Season Analysis", "Men's Soccer &middot; Team-Level Performance Analysis")

st.caption(
    f"What actually separates wins from losses across {len(df)} matches "
    f"({', '.join(selected_seasons)}) — built from Wyscout team-match data."
)
st.info(
    f"Currently showing {len(df)} matches across {len(selected_seasons)} season(s). "
    "Use the sidebar to compare a single season against the full multi-year picture — "
    "some patterns (like the finishing gap) hold up across every season; others "
    "(like the home/away gap) look strong in one season and shrink once more are added.",
    icon="ℹ️",
)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Record", f"{(df['Result']=='Win').sum()}W-{(df['Result']=='Draw').sum()}D-{(df['Result']=='Loss').sum()}L")
col2.metric("Goals For", int(df["GoalsFor"].sum()))
col3.metric("Goals Against", int(df["GoalsAgainst"].sum()))
col4.metric("Total xG", round(df["xG"].sum(), 1))

st.markdown("---")

# ---------------------------------------------------------------------------
# SECTION 1: FINISHING GAP
# ---------------------------------------------------------------------------
section_header("1. The Finishing Gap")
st.markdown(
    "**Question:** Do losses happen because Creighton fails to create chances, "
    "or fails to finish the chances they create?"
)

finishing = df.groupby("Result")[["xG", "xG_diff", "GoalsFor"]].mean().round(2).reindex(["Win", "Draw", "Loss"])
finishing.columns = ["Avg xG Created", "Avg xG Over/Under-performance", "Avg Goals Scored"]

c1, c2 = st.columns([1, 2])
with c1:
    st.dataframe(finishing, use_container_width=True)
    st.caption(
        "In losses, chances created (xG) is close to draws — the real gap "
        "is finishing. Wins show slight overperformance; losses show a "
        "full-goal underperformance on average."
    )

with c2:
    st.markdown("**xG vs Actual Goals, by Match**")
    fig1 = go.Figure()
    fig1.add_trace(go.Bar(x=df["Opponent"] + " (" + df["Result"].str[0] + ")", y=df["xG"], name="xG (chances created)", marker_color=CU_LIGHT_BLUE))
    fig1.add_trace(go.Bar(x=df["Opponent"] + " (" + df["Result"].str[0] + ")", y=df["GoalsFor"], name="Goals Scored", marker_color=CU_NAVY))
    fig1.update_layout(barmode="group", height=400, margin=dict(t=30))
    st.plotly_chart(fig1, use_container_width=True)

st.subheader("Does the finishing gap hold up across every season?")
by_season = df.groupby(["Season", "Result"])["xG_diff"].mean().reset_index()
fig1b = px.bar(
    by_season, x="Season", y="xG_diff", color="Result", barmode="group",
    category_orders={"Result": ["Win", "Draw", "Loss"]},
    color_discrete_map=RESULT_COLORS,
    labels={"xG_diff": "Avg xG Over/Under-performance"},
)
fig1b.add_hline(y=0, line_dash="dot", line_color="gray")
fig1b.update_layout(margin=dict(t=30))
st.plotly_chart(fig1b, use_container_width=True)
st.caption(
    "Losses (red bar per group) sit below zero in every single season — "
    "this pattern isn't a one-year fluke, it repeats across rosters and years."
)

st.markdown("---")

# ---------------------------------------------------------------------------
# SECTION 2: HOME / AWAY SPLIT
# ---------------------------------------------------------------------------
section_header("2. Home vs. Away")
st.markdown("**Question:** Does location change how Creighton performs — offensively or defensively?")

c1, c2 = st.columns(2)

with c1:
    home_away = df.groupby("HomeAway")[["xG", "xG_diff", "GoalsFor", "GoalsAgainst"]].mean().round(2)
    st.dataframe(home_away, use_container_width=True)
    st.caption(
        "Note: this gap looked much larger (roughly 4x) when only 2025 was "
        "included. With more seasons added, the effect shrinks a lot — "
        "worth mentioning if this comes up, since it shows how much a single "
        "season can mislead on its own."
    )

with c2:
    st.markdown("**Results by Location**")
    results_by_location = df.groupby(["HomeAway", "Result"]).size().reset_index(name="Matches")
    fig2 = px.bar(
        results_by_location, x="HomeAway", y="Matches", color="Result", barmode="stack",
        category_orders={"Result": ["Win", "Draw", "Loss"], "HomeAway": ["Home", "Away"]},
        color_discrete_map=RESULT_COLORS,
        labels={"HomeAway": "Location"},
    )
    fig2.update_layout(margin=dict(t=30))
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# ---------------------------------------------------------------------------
# SECTION 3: PPDA (PRESSING INTENSITY)
# ---------------------------------------------------------------------------
section_header("3. Pressing Intensity (PPDA)")
st.markdown(
    "**Question:** Is pressing intensity a leading indicator of results? "
    "(Lower PPDA = more aggressive pressing — fewer opponent passes allowed "
    "before a defensive action.)"
)

if "PPDA" in df.columns:
    c1, c2 = st.columns([1, 2])
    with c1:
        ppda_summary = df.groupby("Result")["PPDA"].agg(["mean", "std", "count"]).round(2).reindex(["Win", "Draw", "Loss"])
        st.dataframe(ppda_summary, use_container_width=True)
        st.caption(
            "No clean pattern here yet — averages are close across results "
            "and overlap heavily once you account for variation. Worth "
            "revisiting as more matches come in, but not a strong signal "
            "at this sample size."
        )
    with c2:
        st.markdown("**PPDA Across the Season**")
        fig3 = px.line(
            df, x="Date", y="PPDA", markers=True, color="Result",
            category_orders={"Result": ["Win", "Draw", "Loss"]},
            color_discrete_map=RESULT_COLORS,
        )
        fig3.update_layout(margin=dict(t=30))
        st.plotly_chart(fig3, use_container_width=True)
else:
    st.info("PPDA not available in this dataset.")

st.markdown("---")

# ---------------------------------------------------------------------------
# SECTION 4: THE 2022 BLUEPRINT & HIDDEN FACTORS
# ---------------------------------------------------------------------------
section_header("4. The 2022 Blueprint & Hidden Factors")
st.markdown(
    "**Question:** What actually separated the 2022 Elite Eight run, and what "
    "are the overlooked factors — good and bad — behind Creighton's results "
    "across all four complete seasons (2022–2025)?"
)

try:
    df_full = pd.read_csv("creighton_full_combined.csv")
    df_full["Season"] = df_full["Season"].astype(str)

    st.subheader("The clearest pattern: possession doesn't predict winning — it goes the other way")
    poss_by_season = df_full[df_full["Result"].isin(["Win", "Loss"])].groupby(["Season", "Result"])["Possession_pct"].mean().reset_index()
    fig4 = px.bar(
        poss_by_season, x="Season", y="Possession_pct", color="Result", barmode="group",
        category_orders={"Result": ["Win", "Loss"]},
        color_discrete_map=RESULT_COLORS,
        labels={"Possession_pct": "Possession %"},
    )
    fig4.update_layout(margin=dict(t=30))
    st.plotly_chart(fig4, use_container_width=True)
    st.caption(
        "Every single season, Creighton had MORE possession in losses than in wins. "
        "This holds across all four years — it's not a one-season fluke."
    )

    st.subheader("The Habits That Separate Wins from Losses")
    st.caption(
        "Each number below is a per-game average — take every match of that type "
        "(e.g. every 2023–25 loss), average Wyscout's own per-match count for that "
        "action across all of them, and that's the number shown. "
        "Win/Loss averages use only 2023–2025 so the 2022 blueprint season doesn't "
        "blend into — and skew — the baseline; 2022 is shown as its own column instead."
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
    st.dataframe(win_loss, use_container_width=True)
    st.caption(
        "Current-era losses involve more individual 1v1 duels and more crosses into "
        "the box — signs of forcing things individually rather than combination play. "
        "Current-era wins convert a bigger share of their structured build-up "
        "possessions into an actual shot. The two 2022 columns are split by result the "
        "same way, so you can compare like with like: 2022's wins against today's wins, "
        "and 2022's losses against today's losses."
    )

    st.subheader("2022's real signature: creative passing volume, not just talent")
    smart_by_season = df_full.groupby("Season")[["SmartPasses", "SmartPassesAccurate"]].mean().round(2).reset_index()
    fig5 = px.bar(
        smart_by_season, x="Season", y=["SmartPasses", "SmartPassesAccurate"], barmode="group",
        labels={"value": "Smart Passes per Game", "variable": "Metric"},
        color_discrete_sequence=[CU_LIGHT_BLUE, CU_NAVY],
    )
    fig5.update_layout(margin=dict(t=30))
    st.plotly_chart(fig5, use_container_width=True)
    st.warning(
        "Honest caveat: 2022 had nearly 2.5x the smart-pass volume of any other season — "
        "a real signature of that roster's identity. But smart passes only clearly predicted "
        "winning WITHIN a season in 2022 and 2024, not 2023 or 2025. Read this as 'that team's "
        "specific style worked for them,' not as a universal 'more smart passes = more wins' rule.",
        icon="⚠️",
    )

except FileNotFoundError:
    st.info("Add creighton_full_combined.csv to this folder to see the deep-dive section.")

st.markdown("---")

# ---------------------------------------------------------------------------
# SECTION 5: STYLE FINGERPRINT (opponent-adjusted PCA)
# ---------------------------------------------------------------------------
section_header("5. Style Fingerprint — Opponent-Adjusted")
st.markdown(
    "**Question:** What does the current era's game (2023–2025) actually look like "
    "relative to who they're playing, and where would the 2022 blueprint season land "
    "on that same map — as a target to compare against, not blended into it?"
)

with st.expander("📖 How to read this section (start here)", expanded=True):
    st.markdown(
        """
This section answers a different question than the ones above it. Instead of
looking at one stat at a time (like "does more possession help us win?"),
it asks: **if you looked at everything at once — passing, shooting, duels,
crosses, all of it — what are the one or two BIGGEST underlying patterns
that separate how a game went?**

**Step 1 — Every stat becomes "us vs. them."**
Instead of "Creighton had 55% possession," we use "Creighton had 3% MORE
possession than this specific opponent." We do that for every single stat.
This matters because 55% possession means something different against a
possession-heavy power vs. a weak team that sits back — the raw number
alone doesn't tell you if Creighton actually dominated *that* game.

**Step 2 — Find the biggest recurring pattern automatically, using ONLY the current era.**
A lot of those "us vs. them" numbers move together. A team that outpasses
its opponent also tends to out-cross them and get into the box more via
passing. So instead of you manually squinting at 85 stats, the model finds
the one big underlying pattern that most of them share, and boils it down
to a single number per match. **This pattern is built using only 2023–2025**
— 2022 is deliberately left out of that step so its unusual style doesn't
warp the map itself. That number becomes the **horizontal axis (left/right)**
below, and the next-biggest leftover pattern becomes the **vertical axis (up/down)**.

**Step 3 — Then place 2022 onto that same map, as a comparison, not an input.**
Once the map is built from today's teams, 2022's games get plotted onto it
using the exact same rules — showing where that blueprint season would sit
relative to how Creighton plays *now*, without 2022 having any influence
over where the map's axes are in the first place.

**Step 4 — Read the chart like a map, not a stat sheet.**
Each dot is one match. Where a dot sits tells you what kind of game that
was, relative to the opponent — not who won, just *what the game looked
like statistically*. Color tells you who won (current era only). **The
interesting finding is where the colors cluster** — and separately, where
the navy 2022 markers sit relative to those clusters.
        """
    )

try:
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler

    diff_df = pd.read_csv("creighton_differentials.csv")
    diff_df["Season"] = diff_df["Season"].astype(str)
    diff_cols = [c for c in diff_df.columns if c.endswith("_Diff")
                 and c not in ["Goals_Diff", "xG_Diff", "ConcededGoals_Diff"]]
    X_all = diff_df[diff_cols].dropna(axis=1, how="any")
    X_all = X_all.loc[:, X_all.std() > 0.01]

    is_2022 = diff_df["Season"] == "2022"
    X_current = X_all.loc[~is_2022]
    X_2022 = X_all.loc[is_2022]

    # Fit the scaler AND the PCA model using only the current era (2023-2025),
    # then transform 2022 through that same already-fitted model. 2022 never
    # participates in defining the axes — it's placed onto them afterward.
    scaler = StandardScaler().fit(X_current)
    pca = PCA(n_components=2).fit(scaler.transform(X_current))

    current_comps = pca.transform(scaler.transform(X_current))
    comps_2022 = pca.transform(scaler.transform(X_2022))

    diff_df.loc[~is_2022, "PC1"] = current_comps[:, 0]
    diff_df.loc[~is_2022, "PC2"] = current_comps[:, 1]
    diff_df.loc[is_2022, "PC1"] = comps_2022[:, 0]
    diff_df.loc[is_2022, "PC2"] = comps_2022[:, 1]

    AXIS1_NAME = "Build-Up Volume (vs. that opponent)"
    AXIS2_NAME = "Shot & Duel Quality (vs. that opponent)"

    current_df = diff_df.loc[~is_2022]
    blueprint_df = diff_df.loc[is_2022]

    st.markdown("**Current Era (2023–25) Map, with 2022 Placed on It for Comparison**")
    fig6 = go.Figure()
    for result, color in [("Win", RESULT_COLORS["Win"]), ("Draw", RESULT_COLORS["Draw"]), ("Loss", RESULT_COLORS["Loss"])]:
        sub = current_df[current_df["Result"] == result]
        fig6.add_trace(go.Scatter(
            x=sub["PC1"], y=sub["PC2"], mode="markers", name=f"{result} (2023–25)",
            marker=dict(color=color, size=10, opacity=0.75),
            text=sub["Opponent"] + " (" + sub["Season"] + ")", hoverinfo="text",
        ))
    fig6.add_trace(go.Scatter(
        x=blueprint_df["PC1"], y=blueprint_df["PC2"], mode="markers",
        name="2022 (Blueprint Year)",
        marker=dict(color=CU_NAVY, size=13, symbol="diamond",
                     line=dict(color="white", width=1)),
        text=blueprint_df["Opponent"] + " (2022, " + blueprint_df["Result"] + ")", hoverinfo="text",
    ))
    fig6.update_layout(
        height=550,
        margin=dict(l=70, t=40, r=40, b=70),
        xaxis_title=f"← Less {AXIS1_NAME}   |   More {AXIS1_NAME} →",
        yaxis_title=f"← Less {AXIS2_NAME}   |   More {AXIS2_NAME} →",
        legend_title_text="",
    )
    st.plotly_chart(fig6, use_container_width=True)
    st.caption(
        f"All {len(current_df)} matches from 2023–2025 are plotted (colored by result), "
        f"plus all {len(blueprint_df)} matches from 2022 (navy diamonds). "
        f"That's {len(diff_df)} total matches shown — every game in the dataset."
    )

    var_exp = pca.explained_variance_ratio_
    st.caption(
        f"The horizontal axis (Build-Up Volume) explains {var_exp[0]*100:.0f}% of the "
        f"differences between current-era games — the single biggest pattern found. The "
        f"vertical axis (Shot & Duel Quality) explains another {var_exp[1]*100:.0f}%. "
        "Together that's the dominant shape of the current-era data, not the full picture — "
        "plenty of smaller factors aren't shown here."
    )

    loadings = pd.DataFrame(pca.components_.T, index=X_all.columns, columns=["PC1", "PC2"])
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**What actually makes up '{AXIS1_NAME}':**")
        st.caption(
            "Stats that move together to form this axis — mainly passing and box-entry "
            "volume. These numbers look almost identical on purpose: all six are different "
            "ways of counting the same underlying thing (how much Creighton passed the "
            "ball forward), so they rise and fall together and PCA weighs them almost "
            "equally. Shown to 3 decimals so you can see they're close, not identical."
        )
        st.dataframe(loadings["PC1"].sort_values(key=abs, ascending=False).head(6).round(3))
    with c2:
        st.markdown(f"**What actually makes up '{AXIS2_NAME}':**")
        st.caption("Stats that move together to form this axis — mainly shot and duel efficiency:")
        st.dataframe(loadings["PC2"].sort_values(key=abs, ascending=False).head(6).round(3))

    st.subheader("Key Takeaway")
    current_win_pc1 = current_df.loc[current_df["Result"] == "Win", "PC1"].mean()
    current_loss_pc1 = current_df.loc[current_df["Result"] == "Loss", "PC1"].mean()
    blueprint_pc1 = blueprint_df["PC1"].mean()
    st.markdown(
        f"""
Look at where the **green dots (current-era wins)** sit compared to the
**red dots (current-era losses)** on the horizontal axis. Right now, wins
average **{current_win_pc1:.2f}** on this axis and losses average
**{current_loss_pc1:.2f}** — wins sit to the left (less relative build-up
volume than the opponent); losses sit to the right (more relative build-up
volume than the opponent).

In the current era, Creighton's losses typically involve out-passing and
out-crossing the opponent MORE than their wins do. That runs counter to the
usual assumption, but it lines up with the possession finding from Section 4
— heavier ball and territory dominance is, on average, the losing profile
right now, not the winning one. A likely read: this reflects games where
Creighton was chasing the game or facing a low block, racking up passes and
crosses without actually breaking the defense down.

**Where 2022 (the navy diamonds) sits — and what "getting back to it" means:**
the 2022 blueprint season averages **{blueprint_pc1:.2f}** on this same axis —
further right (more relative build-up volume) than even today's losses. In
other words, if the current team played the way 2022 did, the raw style
alone would look like a losing profile by today's standard. That team won
anyway, which points to something else covering for a stylistically risky
approach — almost certainly the finishing edge identified in Section 4 (2022
had the highest smart-pass creativity of any season, and converted chances
at a rate other seasons didn't match). **The practical implication for
replicating 2022: leaning into more build-up volume and creative passing
alone won't recreate that run — it only worked in 2022 because the finishing
quality was there to cash in the extra possession. Without that finishing
level, the same style would more likely resemble today's losses than
today's wins.**
        """
    )

except ImportError:
    st.info("This section needs scikit-learn. Run: pip3 install scikit-learn")
except FileNotFoundError:
    st.info("Add creighton_differentials.csv to this folder to see the style fingerprint.")

page_footer()
