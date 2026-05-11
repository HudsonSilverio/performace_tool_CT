# CLAUDE.md — ClearerThinking Tools Performance Dashboard

## Project Overview
This is a Streamlit dashboard that connects to Google Analytics 4 (GA4) and displays the performance funnel of 96 ClearerThinking.org tools. The full specification is in `prd.md`.

## Tech Stack
- **Python 3.10+**
- **Streamlit** — web framework for the dashboard UI
- **Plotly** — all charts and funnel visualizations
- **Pandas** — data processing and transformations
- **google-analytics-data** — official GA4 API client
- **google-auth** — authentication with Google Cloud

## Project Structure
```
performace_tool_CT/
├── .streamlit/
│   ├── config.toml          # Theme and server config
│   └── secrets.toml          # GA4 credentials (LOCAL ONLY, never commit)
├── assets/
│   └── logo.png              # ClearerThinking logo
├── src/
│   ├── __init__.py
│   ├── ga4_client.py         # GA4 API connection and data fetching
│   ├── data_processing.py    # Data transformation and funnel calculations
│   └── components.py         # Reusable UI components (cards, funnel, header)
├── app.py                    # Main entry point (streamlit run app.py)
├── tools_config.py           # Tool URL-to-name mapping (96 tools)
├── requirements.txt          # Python dependencies
├── prd.md                    # Product requirements document
├── CLAUDE.md                 # This file
├── .gitignore
└── README.md
```

## Key Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
streamlit run app.py

# Run with specific port
streamlit run app.py --server.port 8501
```

## Code Conventions

### Python Style
- Follow **PEP 8** strictly
- Use **type hints** on all function signatures
- Use **docstrings** on all functions and classes
- Max line length: 100 characters
- Use f-strings for string formatting, never .format() or %

### Imports
- Standard library first, then third-party, then local — separated by blank lines
- Never use wildcard imports (`from module import *`)

### Naming
- Functions and variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private functions: prefix with underscore `_helper_function()`

### Error Handling
- Always use try/except around GA4 API calls
- Never show raw Python tracebacks to the user — use `st.error()` with a friendly message
- Log errors with `st.logger` or `logging` module
- Division by zero: return 0.0 instead of raising an error

## GA4 Configuration

### Authentication
- **Local dev:** credentials stored in `.streamlit/secrets.toml`
- **Streamlit Cloud:** credentials stored in app settings → Secrets
- Access credentials via `st.secrets["ga4"]["property_id"]` and `st.secrets["ga4"]["credentials"]`
- **NEVER hardcode** the property ID or credentials in source code
- **NEVER commit** `secrets.toml` to git

### Event Names (exact, case-sensitive — do not change)
```
page_view
Viewed Privacy Policy
Accepted Privacy Policy
Reached Email Ask
Submitted Email
Finished Exercise
```

### GA4 Dimensions Used
```
date, pagePath, eventName, sessionCampaignName,
sessionDefaultChannelGroup, deviceCategory, userGender,
country, userAgeBracket
```

## Streamlit Conventions

### Layout
- Always use `st.set_page_config(layout="wide")` — the dashboard needs full width
- Use `st.sidebar` for all filters
- Use `st.columns()` for KPI cards and grid layouts
- Use custom HTML/CSS via `st.markdown(unsafe_allow_html=True)` for styled components (header, cards, funnel)

### Session State
- Use `st.session_state` to track:
  - `selected_tool` — which tool the user clicked (None = overview page, string = tool detail page)
  - `page` — current page ("overview" or "detail")
- Always initialize session state variables at the top of `app.py`

### Caching
- Use `@st.cache_data(ttl=3600)` for GA4 API calls (1 hour cache)
- Never cache UI components, only data-fetching functions
- Include a "Refresh data" button that calls `st.cache_data.clear()`

### Custom CSS
- Inject all custom CSS at the top of `app.py` using `st.markdown()` with a `<style>` tag
- Use the color palette defined in `prd.md` Section 6.1
- Never use inline styles on Streamlit native components — use CSS classes

## Data Processing Rules

### Tool Identification
- Tools are identified by `pagePath` from GA4
- The mapping from path to human-readable name is in `tools_config.py`
- If a pagePath is not in the mapping, **ignore it** — do not show it in the dashboard
- Match paths using `str.contains()` or `str.endswith()` to handle variations

### Funnel Calculations
- Completion rate = Finished Exercise / Viewed Privacy Policy
- Email rate = Submitted Email / Viewed Privacy Policy
- Drop-off between steps = 1 - (step_N / step_N-1)
- If denominator is 0, return 0.0

### Previous Period
- Always calculate based on the same number of days
- If selected range is 30 days, previous period is the 30 days before
- Change % = ((current - previous) / previous) * 100
- If previous is 0, show "N/A"

### Card Border Colors
- Green (#1D9E75): completion rate >= 10%
- Amber (#BA7517): completion rate >= 5% and < 10%
- Red (#E24B4A): completion rate < 5%

## Git Rules
- **Never commit:** `.streamlit/secrets.toml`, `*.pyc`, `__pycache__/`, `.env`
- **Always commit:** `requirements.txt`, `config.toml`, all `.py` files, `prd.md`, `CLAUDE.md`
- Write clear commit messages in English
- The `.gitignore` must include:
```
.streamlit/secrets.toml
__pycache__/
*.pyc
.env
.venv/
venv/
*.egg-info/
dist/
build/
```

## Testing & Validation
- After making any change, run `streamlit run app.py` to verify it works
- Verify that funnel numbers match GA4 reports for the same date range
- Test with different filter combinations to ensure no errors
- Test with date ranges that return zero data — should show friendly "No data" message

## Common Pitfalls
- GA4 API returns `(not set)` for unknown gender/age — display as "Not set" in filters
- GA4 pagePath may or may not start with `/` — normalize all paths to start with `/`
- The API has a 10,000 row default limit — always set `limit=250000` and handle pagination
- Streamlit reruns the entire script on every interaction — keep expensive operations in cached functions
- `st.session_state` persists across reruns but resets on page refresh