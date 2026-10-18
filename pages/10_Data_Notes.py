import pandas as pd
import streamlit as st
from branding import CU_NAVY, section_header, page_banner, page_footer, page_nav, HIDDEN_PAGES

st.set_page_config(page_title="Creighton Bluejays — Data Notes", layout="wide", page_icon="🔵")

page_banner("Data Notes", "Men's Soccer &middot; What the data covers, what's missing, and how to read the findings")
page_nav("pages/10_Data_Notes.py")
st.markdown("---")

# ---------------------------------------------------------------------------
section_header("What the data covers")
try:
    m = pd.read_csv("creighton_matches_combined.csv")
    per_season = m.groupby("Season").size()
    counts = ", ".join(f"{s}: {n}" for s, n in per_season.items())
except FileNotFoundError:
    counts = "n/a"

sources = pd.DataFrame([
    ["Team match statistics", "2022–2026 (Wyscout)", f"One row per match. Matches per season: {counts}. 2026 is in progress."],
    ["Opponent chances (xG against)", "2022–2026", "From the opponent rows in the same Wyscout team exports."],
    ["Player match-by-match", "2021–2025 (Wyscout)", "Every match for every player. It is no longer used on any page; the 2026 pages use the window reports instead."],
    ["2026 player statistics", "Aug 23 – Sep 8 and Sep 19 – Oct 3", "Two five-match Wyscout team reports (10 of 13 matches). The Aug 21 (FIU), Sep 11 (St. Mary's) and Sep 13 (Yale) matches are not in any export yet."],
    ["Formation and competition", "2022–2026", "Scheme (formation) and competition for each match, from the same team exports. Used on the 2026 page."],
    ["2026 rotation", "Same two windows", "Starts, substitute appearances and minutes per player, taken from the two five-match reports."],
    ["2026 roster", "gocreighton.com", "29 players. Four have no recorded minutes yet, and goalkeepers are not in Wyscout's outfield table."],
], columns=["Data", "Coverage", "Notes"])
st.table(sources.set_index("Data"))

# ---------------------------------------------------------------------------
section_header("What it can't tell us yet")
st.markdown(
    """
- **2026 match-to-match consistency.** 2026 player data comes as two multi-match windows, so a match-by-match steadiness score isn't possible for this season. A 2026 match-by-match player export in the same format as 2021–2025 would fix this.
- **Where on the pitch things happen.** Wyscout's team and player summaries have no event locations, so measures like expected threat or pitch control aren't possible.
- **Physical load.** There is no GPS data. The Workload What-If page is a prototype that uses simulated numbers and says so on the page.
- **Cause and effect.** Most findings compare groups of matches (wins vs. losses, with vs. without a player). That shows how games differed, not why. Game state, opponent strength and luck all play a part, and a single season rarely has enough matches to separate them.
- **Opponent strength.** Results are not adjusted for who Creighton played.
    """
)

# ---------------------------------------------------------------------------
section_header("How to read the evidence tags")
st.markdown(
    """
Findings on the dashboard carry a tag and a sample size, for example *Evidence: Moderate · 83 matches*.

- **Clear:** a consistent result across seasons with a reasonable number of matches.
- **Moderate:** the direction is consistent, but the sample is modest or part of the result is built in.
- **Suggestive:** a pattern worth watching, based on a small sample or a single season.
- **Low:** a handful of matches. Interesting, not a basis for a decision.
- **Descriptive:** states what happened without claiming a reason.
    """
)

# ---------------------------------------------------------------------------
section_header("Glossary")
glossary = pd.DataFrame([
    ["xG (expected goals)", "The chance of each shot becoming a goal, based on shot location and type, summed for the match. A measure of chance quality."],
    ["xG against", "The same measure for the chances Creighton's opponent created."],
    ["Goals minus xG", "Goals scored minus xG created. Positive means scoring more than the chances suggested."],
    ["Per 90", "A player's total scaled to 90 minutes, so players with different minutes can be compared."],
    ["PPDA", "Opponent passes allowed per defensive action in the opponent's final 60% of the pitch. Lower means more aggressive pressing."],
    ["Smart pass", "Wyscout's label for a pass that tries to break through the defense, such as a through ball."],
    ["Consistency (CV)", "How much a player's per-90 rate varies from match to match, relative to their average. Lower is steadier."],
    ["Build-up volume score", "A single number summarizing how much more (or less) Creighton passed and entered the box than the opponent in a match. Built from the differences between the two teams' passing and box-entry counts."],
], columns=["Term", "Meaning"])
st.table(glossary.set_index("Term"))

# ---------------------------------------------------------------------------
section_header("Prototype")
for path, label, desc in HIDDEN_PAGES:
    st.page_link(path, label=label)
    st.caption(desc)

page_footer()
