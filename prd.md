# PRD — ClearerThinking Tools Performance Dashboard

## 1. Overview

Build a professional, real-time dashboard in Python (Streamlit) that connects to the ClearerThinking.org GA4 property and displays the performance funnel of all 96 tools. The dashboard must be so clear that a CEO can look at it for 10 seconds and understand what is happening.

**Tech stack:** Python 3.10+, Streamlit, Plotly, Google Analytics Data API (GA4)
**Deploy:** Streamlit Community Cloud (free) — https://share.streamlit.io
**Repo:** https://github.com/HudsonSilverio/performace_tool_CT

---

## 2. GA4 Configuration

### 2.1 Authentication
- Use a **Google Cloud Service Account** with a JSON key file
- The service account must have **Viewer** role in the GA4 property
- The GA4 Property ID will be stored as an environment variable: `GA4_PROPERTY_ID`
- The service account JSON key will be stored as a Streamlit secret (for cloud deploy) or as a local file (for dev)

### 2.2 Event Names (exact, case-sensitive)
These are the custom events configured in GA4 that form the user funnel:

1. `page_view` — user landed on the tool page
2. `Viewed Privacy Policy` — entered the tool
3. `Accepted Privacy Policy` — went to the second page
4. `Reached Email Ask` — reached the email request
5. `Submitted Email` — inserted an email
6. `Finished Exercise` — completed the tool

### 2.3 Tool Identification
Tools are identified by their `page_path` dimension in GA4. Each tool has a unique URL path. The full list of 96 tool paths is in Section 8 below.

### 2.4 GA4 Dimensions Required for Filters
- `date` — for date range filtering
- `pagePath` — to identify which tool
- `sessionCampaignName` — Campaign filter
- `sessionDefaultChannelGroup` — Channel filter
- `deviceCategory` — Device filter (desktop, mobile, tablet)
- `userGender` — Gender filter
- `country` — Country filter
- `userAgeBracket` — Age filter

### 2.5 GA4 Metrics
- `eventCount` — count of each event
- `totalUsers` — unique users

---

## 3. Dashboard Structure

The dashboard has **2 pages** with a shared filter sidebar.

### 3.1 Page 1: Overview (Tools Grid)

**Layout:**
- **Header bar** (top, full width): Blue background (#1A73E8), ClearerThinking logo on the left, title "Tools performance dashboard" next to it, navigation tabs (Overview / Tool detail) on the right
- **Filter sidebar** (left, 200px wide): All 7 filters stacked vertically (see Section 5)
- **Main content area** (right of sidebar): KPI summary cards at top, then a grid of tool cards

**KPI Summary Cards (4 cards in a row at the top of main area):**
1. **Total users** — sum of `totalUsers` across all tools for the selected period. Show comparison % vs previous period.
2. **Avg completion rate** — average of (Finished Exercise / Viewed Privacy Policy) across all tools. Show comparison % vs previous period.
3. **Finished exercise** — sum of `eventCount` where event = "Finished Exercise" across all tools. Show comparison % vs previous period.
4. **Submitted email** — sum of `eventCount` where event = "Submitted Email" across all tools. Show comparison % vs previous period.

**Color Legend (below KPI cards, above the grid):**
Display a horizontal legend explaining the card border colors:
- 🟢 Green (#1D9E75) = completion rate above 10%
- 🟠 Amber (#BA7517) = completion rate between 5% and 10%
- 🔴 Red (#E24B4A) = completion rate below 5%

**Tool Cards Grid:**
- Display all 96 tools as cards in a responsive grid (4 columns on desktop, 2 on mobile)
- Cards are **sorted by completion rate, descending** (best performers first)
- Each card shows:
  - Tool name (human-readable, derived from the page_path — see Section 8 for mapping)
  - Main KPI number: count of "Finished Exercise" events (large font)
  - Word "finished" next to the number (small, colored text)
  - Completion rate as percentage (Finished Exercise / Viewed Privacy Policy)
  - Trend indicator: ▲ or ▼ with % change vs previous period
  - Mini sparkline chart showing daily "Finished Exercise" count over the selected period
  - **Left border color** based on completion rate thresholds (green / amber / red)
- Pagination: show 8 tools per page (configurable), with page numbers at the bottom
- **Clicking a card navigates to Page 2** with that tool pre-selected

### 3.2 Page 2: Tool Detail (Funnel View)

**Layout:**
- Same header bar as Page 1, but "Tool detail" tab is highlighted
- Same filter sidebar on the left
- Main content area shows the selected tool's funnel

**Top Section:**
- "← Back to overview" button (navigates back to Page 1)
- Tool name (large, bold)
- Tool URL path (small, gray, below the name)

**KPI Cards (4 cards in a row):**
1. **Total users entered** — `eventCount` for "Viewed Privacy Policy" for this tool. Show comparison % vs previous period.
2. **Completion rate** — Finished Exercise / Viewed Privacy Policy for this tool. Show comparison % vs previous period. Color the number green if positive trend, red if negative.
3. **Email submission rate** — Submitted Email / Viewed Privacy Policy for this tool. Show comparison % vs previous period.
4. **Finished exercise** — `eventCount` for "Finished Exercise" for this tool. Show comparison % vs previous period.

**Funnel Visualization:**
- 5 horizontal bars stacked vertically, each representing one funnel step
- Each bar shows:
  - Step name (left side, white text on colored background)
  - User count (right side of bar, white text)
  - Percentage relative to total users entered (right side, outside the bar)
- Bar widths are proportional to the user count at each step (first bar = 100% width)
- Between each bar, show the **drop-off percentage** (e.g., "↓ 58.5% drop-off")
- Color scheme for bars (top to bottom):
  - Step 1: #1A73E8 (dark blue)
  - Step 2: #3D8BE8
  - Step 3: #6BA8E5
  - Step 4: #93C1F0 (light blue, with dark text #042C53)
  - Step 5: #1D9E75 (green — represents completion)
- Below the funnel, show a legend with color meanings

**Funnel steps in order:**
1. Viewed Privacy Policy
2. Accepted Privacy Policy
3. Reached Email Ask
4. Submitted Email
5. Finished Exercise

---

## 4. Data Loading & Caching

- **Default date range:** Last 30 days from today
- **Data freshness:** Load real-time data from GA4 API on each page load
- **Caching:** Use `@st.cache_data(ttl=3600)` to cache API responses for 1 hour to avoid hitting API rate limits. Add a "Refresh data" button that clears the cache and reloads.
- **Previous period calculation:** If the user selects a 30-day range (Mar 25 – Apr 23), the previous period is the 30 days before that (Feb 23 – Mar 24). Always match the same number of days.
- **API pagination:** GA4 API returns max 10,000 rows per request. Implement pagination if needed for large date ranges.

---

## 5. Filters

All filters are in the left sidebar and apply to both pages. All filters default to "All" (no filter applied).

| Filter | GA4 Dimension | UI Control |
|--------|--------------|------------|
| Date range | `date` | Date range picker (default: last 30 days) |
| Campaign | `sessionCampaignName` | Multi-select dropdown |
| Channel | `sessionDefaultChannelGroup` | Multi-select dropdown |
| Device | `deviceCategory` | Multi-select dropdown |
| Gender | `userGender` | Multi-select dropdown |
| Country | `country` | Multi-select dropdown |
| Age | `userAgeBracket` | Multi-select dropdown |

---

## 6. Styling & Branding

### 6.1 Color Palette
- Primary blue: #1A73E8
- Green (success/good): #1D9E75
- Amber (warning/medium): #BA7517
- Red (danger/poor): #E24B4A
- Background: #F8F8F8
- Card background: #FFFFFF
- Border: #E0E0E0
- Text primary: #222222
- Text secondary: #999999
- Sidebar background: #FFFFFF

### 6.2 Typography
- Use Streamlit's default font
- KPI numbers: large (24-28px equivalent), font-weight 500
- Card titles: 14px equivalent, font-weight 500
- Labels: 12px equivalent, color #999999
- Comparison percentages: 11px, green for positive, red for negative

### 6.3 Layout
- Total page width: full width (Streamlit wide mode)
- Sidebar width: Streamlit's default sidebar
- Header: custom HTML/CSS component at the top
- Cards: use Streamlit columns and custom HTML/CSS for styling

### 6.4 Logo
- The ClearerThinking logo should be displayed in the header
- Store as `assets/logo.png` in the project
- The user will provide this file

### 6.5 Streamlit Theme Config
Create `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#1A73E8"
backgroundColor = "#F8F8F8"
secondaryBackgroundColor = "#FFFFFF"
textColor = "#222222"
font = "sans serif"

[server]
headless = true

[browser]
gatherUsageStats = false
```

---

## 7. Project Structure

```
performace_tool_CT/
├── .streamlit/
│   ├── config.toml          # Streamlit theme configuration
│   └── secrets.toml          # GA4 credentials (local dev only, DO NOT commit)
├── assets/
│   └── logo.png              # ClearerThinking logo (user provides)
├── src/
│   ├── __init__.py
│   ├── ga4_client.py         # GA4 API connection and data fetching
│   ├── data_processing.py    # Data transformation, funnel calculations, comparisons
│   └── components.py         # Reusable UI components (cards, funnel chart, header)
├── app.py                    # Main Streamlit app (entry point)
├── tools_config.py           # Tool names, URL paths, and mapping
├── requirements.txt          # Python dependencies
├── .gitignore                # Ignore secrets, cache, etc.
└── README.md                 # Setup and deploy instructions
```

---

## 8. Tool Path-to-Name Mapping

The dashboard must map raw GA4 `page_path` values to human-readable tool names. Below is the complete mapping of all 96 tools:

```python
TOOLS_MAP = {
    "/unique-traits-test/": "Unique Traits Test",
    "/understanding-your-morality": "Understand Your Morality",
    "/imposter_syndrome.html": "The Imposter Syndrome Test",
    "/social_biases.html": "How Other People Can Make You Irrational",
    "/flexible_thinking.html": "Flexible Thinking",
    "/predict_correlations.html": "Predict Psychological Correlations",
    "/productive_disagreement.html": "Productive Disagreements",
    "/retrocaster.html": "Retrocaster",
    "/faulty_reasoning_quiz.html": "Faulty Reasoning Quiz",
    "/biosafety_quiz.html": "Biosafety Quiz",
    "/make_your_work_more_joyful.html": "Make Your Work More Joyful",
    "/kind_and_effective_communication.html": "Kind and Effective Communication",
    "/effective_trust_repair.html": "Effective Trust Repair",
    "/emotional_obstacles_to_doing_good.html": "Emotional Obstacles to Doing Good",
    "/worlds_biggest_problems_quiz.html": "World's Biggest Problems Quiz",
    "/political_bias_test.html": "Political Bias Test",
    "/question_your_identity.html": "Question Your Identity",
    "/EARR_framework.html": "Resolve Harmful Situations",
    "/savoring.html": "Savor Your Life",
    "/skeptical_seekers.html": "Are You a Skeptic or a Seeker?",
    "/tactics_for_happier_living.html": "Tactics for Happier Living",
    "/common_misconceptions.html": "The Common Misconceptions Test",
    "/decisionmaker.html": "The Decision Advisor",
    "/hidden_meaning_of_sounds.html": "The Hidden Meaning of Sounds",
    "/planning_fallacy.html": "The Planning Fallacy",
    "/relationship_review.html": "The Relationship Review",
    "/understanding_bayes_theorem.html": "Understanding Bayes Theorem",
    "/what_causes_match_your_values.html": "What Causes Match Your Values?",
    "/what_to_know_about_suicide.html": "What to Know About Suicide",
    "/when_to_stop_exploring.html": "When To Stop Exploring",
    "/your_primal_world_beliefs.html": "Your Primal World Beliefs",
    "/spark_the_mood_you_want.html": "Spark the Mood You Want",
    "/achieve_your_goals.html": "Achieve Your Goals",
    "/boost_your_productivity.html": "Boost Your Productivity",
    "/career_fulfillment_diagnostic.html": "Career Fulfillment Diagnostic",
    "/can_you_guess_which_charities_work.html": "Charity Effectiveness",
    "/daily_ritual.html": "Daily Ritual: A Habit Creation System",
    "/design_your_own_self_experiment.html": "Design Your Own Self-Experiment",
    "/explanation_freeze.html": "Explanation Freeze",
    "/gender_continuum_test.html": "Gender Continuum Test",
    "/how_rational_are_you_really_take_the_test.html": "How Rational Are You, Really?",
    "/is_your_memory_like_a_photograph.html": "Is Your Memory Like A Photograph?",
    "/mistakes.html": "Learning From Mistakes",
    "/lcq.html": "Life Changing Questions",
    "/managing_arguments.html": "Managing Arguments in Relationships",
    "/moodboosters.html": "Mood Boosters",
    "/Cognitive_Defusion": "Step Back From Your Thoughts",
    "/how-to-compliment.html": "Craft Perfect Compliments",
    "/cognitive-test-intro.html": "Cognitive Assessment",
    "/cult_assessment.html": "The Cult Assessment",
    "/astrology_challenge.html": "The Astrology Challenge",
    "/create_your_custom_clearer_thinking_plan.html": "Clearer Thinking Paths",
    "/personality.html": "The Ultimate Personality Test",
    "/nuanced_thinking_techniques.html": "Nuanced Thinking Techniques",
    "/pathkeeper_intro.html": "Pathkeeper",
    "/practice_self-compassion.html": "Practice Self-Compassion",
    "/art_of_collaboration.html": "The Art of Collaboration",
    "/long-term_future_quiz.html": "Long-Term Future Quiz",
    "/artificial_intelligence_quiz.html": "Artificial Intelligence Quiz",
    "/your_quarterly_life_review.html": "Your Quarterly Life Review",
    "/uncover_your_guiding_principles.html": "Uncover Your Guiding Principles",
    "/program_yourself.html": "Program Yourself to Improve Your Life",
    "/reframing_negative_emotions.html": "Reframing Negative Emotions",
    "/rhetorical_fallacies.html": "Rhetorical Fallacies",
    "/seek_criticism_tool.html": "Seeking Outside Criticism",
    "/surpass_self-limiting-beliefs.html": "Surpass Self-Limiting Beliefs",
    "/challenge_your_deepest_beliefs.html": "The Belief Challenger",
    "/confrontation_aid.html": "The Confrontation Aid",
    "/would_you_make_a_good_tech_startup_founder.html": "The Entrepreneur Test",
    "/intrinsic_values_test.html": "The Intrinsic Values Test",
    "/question_of_evidence.html": "The Question of Evidence",
    "/sunk_costs.html": "The Sunk Cost Fallacy",
    "/what_is_your_time_really_worth_to_you.html": "Value Of Your Time Calculator",
    "/goal_trainer_ct.html": "What Makes an Effective Goal?",
    "/should_you_trust_your_thinking.html": "When Are You Overconfident?",
    "/sources_of_pleasure.html": "Your Greatest Sources of Pleasure",
    "/replace_unhelpful_coping_strategies.html": "Replace Unhelpful Coping Strategies",
    "/40_winks.html": "40 Winks: Better Sleep Made Easy",
    "/become_a_great_listener.html": "Become A Great Listener",
    "/building_happiness_habits.html": "Building Happiness Habits",
    "/can_you_detect_weak_arguments.html": "Can You Detect Weak Arguments?",
    "/change_behavior.html": "Change Behavior for the Better",
    "/credentialist_test.html": "Credentialist Test",
    "/defining_emotions.html": "Defining Emotions",
    "/enhancing_creativity.html": "Enhancing Creativity",
    "/fail-safing_your_plans.html": "Fail-Safing Your Plans",
    "/overcome_procrastination.html": "Get Going: Overcome Procrastination",
    "/how_well_anchored_are_your_estimates.html": "How Airtight Are Your Estimates?",
    "/improve_your_frequency_predictions.html": "Improve Your Frequency Predictions",
    "/philosophical_beliefs.html": "Learn Your Philosophical Beliefs",
    "/how_to_do_more_good.html": "Leaving Your Mark on the World",
    "/life_assessment.html": "Lifetime Aspirations",
    "/introduction.html": "Mental Traps",
    "/overconfidence_analyzer.html": "Overconfidence Analyzer",
    "/personality-test.html": "Personality Test",
    "/advanced-cognitive-assessment": "Advanced Cognitive Assessment",
}
```

**Note:** Some tools have paths that don't end in `.html` (like `/unique-traits-test/`, `/understanding-your-morality`, `/Cognitive_Defusion`, `/advanced-cognitive-assessment`). The matching logic should handle both formats. Also, two external tools exist:
- Calibrate Your Judgment: `https://www.openphilanthropy.org/calibration` — EXCLUDE (external site)
- Guess Which Experiments Replicate: `https://80000hours.org/psychology-replication-quiz/` — EXCLUDE (external site)

These 2 are hosted on external domains and will not appear in ClearerThinking's GA4 data, so exclude them.

---

## 9. Key Calculations

### 9.1 Completion Rate (per tool)
```
completion_rate = event_count("Finished Exercise") / event_count("Viewed Privacy Policy")
```
If "Viewed Privacy Policy" count is 0, set completion rate to 0%.

### 9.2 Email Submission Rate (per tool)
```
email_rate = event_count("Submitted Email") / event_count("Viewed Privacy Policy")
```

### 9.3 Drop-off Between Funnel Steps
```
dropoff_step_N = 1 - (event_count_step_N / event_count_step_N-1)
```
Example: If step 1 has 42,850 and step 2 has 17,783:
```
dropoff = 1 - (17,783 / 42,850) = 58.5%
```

### 9.4 Previous Period Comparison
```
selected_days = (end_date - start_date).days + 1
previous_start = start_date - timedelta(days=selected_days)
previous_end = start_date - timedelta(days=1)
change_pct = ((current_value - previous_value) / previous_value) * 100
```
If previous_value is 0, show "N/A" instead of a percentage.

### 9.5 Card Border Color Thresholds
```python
def get_performance_color(completion_rate):
    if completion_rate >= 0.10:  # 10%+
        return "#1D9E75"  # Green
    elif completion_rate >= 0.05:  # 5-10%
        return "#BA7517"  # Amber
    else:  # Below 5%
        return "#E24B4A"  # Red
```

---

## 10. GA4 API Implementation Details

### 10.1 Python Library
Use `google-analytics-data` (official Google library):
```python
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest, DateRange, Dimension, Metric, FilterExpression, Filter
)
```

### 10.2 API Query Strategy
Make **one API call** that returns all events for all tool pages in the selected date range, with all dimensions needed for filtering:

```python
request = RunReportRequest(
    property=f"properties/{PROPERTY_ID}",
    date_ranges=[DateRange(start_date="2026-03-25", end_date="2026-04-23")],
    dimensions=[
        Dimension(name="date"),
        Dimension(name="pagePath"),
        Dimension(name="eventName"),
        Dimension(name="sessionCampaignName"),
        Dimension(name="sessionDefaultChannelGroup"),
        Dimension(name="deviceCategory"),
        Dimension(name="userGender"),
        Dimension(name="country"),
        Dimension(name="userAgeBracket"),
    ],
    metrics=[
        Metric(name="eventCount"),
    ],
    dimension_filter=FilterExpression(
        filter=Filter(
            field_name="eventName",
            in_list_filter=Filter.InListFilter(
                values=[
                    "page_view",
                    "Viewed Privacy Policy",
                    "Accepted Privacy Policy",
                    "Reached Email Ask",
                    "Submitted Email",
                    "Finished Exercise",
                ]
            ),
        )
    ),
    limit=250000,
)
```

**Important:** The API has a 10,000 row limit per request by default. Use `limit=250000` and handle pagination with `offset` if the response has `row_count` greater than the returned rows.

### 10.3 Data Processing Pipeline
1. Fetch raw data from GA4 API → Pandas DataFrame
2. Filter DataFrame to only include known tool paths (from TOOLS_MAP)
3. Apply user-selected filters (campaign, channel, device, gender, country, age)
4. Pivot data to calculate funnel metrics per tool
5. Calculate completion rates, email rates, comparisons
6. Sort by completion rate descending
7. Pass to UI components for rendering

---

## 11. requirements.txt

```
streamlit>=1.32.0
google-analytics-data>=0.18.0
google-auth>=2.28.0
pandas>=2.2.0
plotly>=5.19.0
```

---

## 12. Deployment Instructions (for README.md)

### Local Development
1. Clone the repo: `git clone https://github.com/HudsonSilverio/performace_tool_CT.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Create `.streamlit/secrets.toml` with your GA4 credentials:
```toml
[ga4]
property_id = "YOUR_GA4_PROPERTY_ID"
credentials = '''
{
  PASTE YOUR ENTIRE SERVICE ACCOUNT JSON KEY HERE
}
'''
```
4. Add your logo file to `assets/logo.png`
5. Run: `streamlit run app.py`

### Streamlit Cloud Deploy
1. Push code to GitHub (do NOT push secrets.toml)
2. Go to https://share.streamlit.io
3. Click "New app" → select your repo → set `app.py` as the main file
4. Go to app settings → Secrets → paste the contents of your `secrets.toml`
5. Click Deploy

---

## 13. Edge Cases & Error Handling

- **No data for a tool:** If a tool has zero events in the selected period, show the card with "0" and "0%" — don't hide it
- **API rate limits:** GA4 API allows 10 requests per second per property. Add retry logic with exponential backoff
- **API timeout:** Set a 30-second timeout. Show a user-friendly error message if it times out
- **Missing dimensions:** If GA4 returns "(not set)" for gender or age, display it as "Not set" in the filter
- **Division by zero:** When calculating rates, if the denominator is 0, return 0% instead of erroring
- **Large date ranges:** For ranges > 90 days, warn the user that loading may take longer
- **Empty filters:** If a filter combination returns no data, show a message: "No data found for the selected filters"

---

## 14. Non-Functional Requirements

- **Load time:** Dashboard should load in under 10 seconds for a 30-day range
- **Responsiveness:** Must work on desktop (1200px+). Mobile is nice-to-have but not required
- **Browser support:** Chrome, Firefox, Safari, Edge (latest versions)
- **Data accuracy:** Numbers must match GA4 reports exactly
- **Code quality:** Clean, commented code. Follow PEP 8 conventions
