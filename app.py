"""ClearerThinking Tools Performance Dashboard — Main entry point."""

from datetime import date, timedelta

import streamlit as st

from src.components import (
    render_color_legend,
    render_funnel_chart,
    render_header,
    render_kpi_card,
    render_pagination,
    render_tool_card,
)
from src.data_processing import (
    apply_filters,
    calculate_change_pct,
    calculate_completion_rate,
    calculate_funnel_metrics,
    calculate_overview_metrics,
    calculate_previous_period,
    get_event_count,
    get_filter_options,
    get_sparkline_data,
    get_tool_summary,
    process_raw_data,
)
from src.ga4_client import fetch_data_for_period
from tools_config import TOOLS_MAP

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="ClearerThinking Tools Dashboard",
    page_icon="📊",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Hide default Streamlit header/footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Card hover */
    div[data-testid="stVerticalBlock"] > div {
        transition: transform 0.1s ease;
    }

    /* Reduce button padding in tool cards */
    .stButton > button {
        padding: 4px 12px;
        font-size: 12px;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = "overview"
if "selected_tool" not in st.session_state:
    st.session_state.selected_tool = None
if "current_page" not in st.session_state:
    st.session_state.current_page = 0


def _navigate_to_detail(tool_key: str) -> None:
    """Navigate to the detail page for a specific tool."""
    st.session_state.page = "detail"
    st.session_state.selected_tool = tool_key


def _navigate_to_overview() -> None:
    """Navigate back to the overview page."""
    st.session_state.page = "overview"
    st.session_state.selected_tool = None

# ---------------------------------------------------------------------------
# Sidebar — Filters
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Filters")

    # Date range
    today = date.today()
    default_start = today - timedelta(days=30)
    date_range = st.date_input(
        "Date range",
        value=(default_start, today),
        max_value=today,
    )

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = default_start, today

    # Refresh button
    if st.button("Refresh data"):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
current_df = fetch_data_for_period(start_date, end_date)
prev_start, prev_end = calculate_previous_period(start_date, end_date)
prev_df = fetch_data_for_period(prev_start, prev_end)

# Check for empty data
if current_df.empty:
    render_header(active_page=st.session_state.page)
    st.warning(
        "No data available. Please check your GA4 credentials "
        "in `.streamlit/secrets.toml` and try again."
    )
    st.stop()

# Process data
current_df = process_raw_data(current_df)
prev_df = process_raw_data(prev_df)

# ---------------------------------------------------------------------------
# Sidebar — Dynamic filters (populated from data)
# ---------------------------------------------------------------------------
with st.sidebar:
    filter_dimensions = {
        "sessionCampaignName": "Campaign",
        "sessionDefaultChannelGroup": "Channel",
        "deviceCategory": "Device",
        "userGender": "Gender",
        "country": "Country",
        "userAgeBracket": "Age",
    }

    active_filters: dict[str, list[str]] = {}

    for dim_key, dim_label in filter_dimensions.items():
        options = get_filter_options(current_df, dim_key)
        selected = st.multiselect(dim_label, options=options, default=[])
        if selected:
            # Map "Not set" back to "(not set)" for filtering
            mapped = ["(not set)" if v == "Not set" else v for v in selected]
            active_filters[dim_key] = mapped

# Apply filters
filtered_df = apply_filters(current_df, active_filters)
filtered_prev_df = apply_filters(prev_df, active_filters)

if filtered_df.empty:
    render_header(active_page=st.session_state.page)
    st.info("No data found for the selected filters.")
    st.stop()

# ---------------------------------------------------------------------------
# Page routing
# ---------------------------------------------------------------------------
if st.session_state.page == "detail" and st.session_state.selected_tool:
    # ===== DETAIL PAGE =====
    render_header(active_page="detail")

    tool_key = st.session_state.selected_tool
    tool_name = TOOLS_MAP.get(tool_key, tool_key)

    # Back button
    if st.button("← Back to overview"):
        _navigate_to_overview()
        st.rerun()

    # Tool title
    st.markdown(
        f"""
        <div style="margin-bottom:20px;">
            <h2 style="margin:0;color:#222;">{tool_name}</h2>
            <span style="font-size:13px;color:#999;">{tool_key}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # KPI cards for this tool
    curr_viewed = get_event_count(filtered_df, "Viewed Privacy Policy", tool_key)
    curr_finished = get_event_count(filtered_df, "Finished Exercise", tool_key)
    curr_email = get_event_count(filtered_df, "Submitted Email", tool_key)
    curr_comp_rate = calculate_completion_rate(curr_finished, curr_viewed)
    curr_email_rate = calculate_completion_rate(curr_email, curr_viewed)

    prev_viewed = get_event_count(filtered_prev_df, "Viewed Privacy Policy", tool_key)
    prev_finished = get_event_count(filtered_prev_df, "Finished Exercise", tool_key)
    prev_email = get_event_count(filtered_prev_df, "Submitted Email", tool_key)
    prev_comp_rate = calculate_completion_rate(prev_finished, prev_viewed)
    prev_email_rate = calculate_completion_rate(prev_email, prev_viewed)

    kpi_cols = st.columns(4)
    with kpi_cols[0]:
        render_kpi_card(
            "Total users entered",
            f"{curr_viewed:,}",
            calculate_change_pct(curr_viewed, prev_viewed),
        )
    with kpi_cols[1]:
        render_kpi_card(
            "Completion rate",
            f"{curr_comp_rate:.1%}",
            calculate_change_pct(curr_comp_rate, prev_comp_rate),
        )
    with kpi_cols[2]:
        render_kpi_card(
            "Email submission rate",
            f"{curr_email_rate:.1%}",
            calculate_change_pct(curr_email_rate, prev_email_rate),
        )
    with kpi_cols[3]:
        render_kpi_card(
            "Finished exercise",
            f"{curr_finished:,}",
            calculate_change_pct(curr_finished, prev_finished),
        )

    # Funnel visualization
    st.markdown("### Funnel")
    funnel_data = calculate_funnel_metrics(filtered_df, tool_key)
    render_funnel_chart(funnel_data)

    # Funnel color legend
    st.markdown(
        """
        <div style="font-size:11px;color:#999;margin-top:8px;">
            <span style="color:#1A73E8;">&#9632;</span> Viewed Privacy Policy &nbsp;
            <span style="color:#3D8BE8;">&#9632;</span> Accepted Privacy Policy &nbsp;
            <span style="color:#6BA8E5;">&#9632;</span> Reached Email Ask &nbsp;
            <span style="color:#93C1F0;">&#9632;</span> Submitted Email &nbsp;
            <span style="color:#1D9E75;">&#9632;</span> Finished Exercise
        </div>
        """,
        unsafe_allow_html=True,
    )

else:
    # ===== OVERVIEW PAGE =====
    render_header(active_page="overview")

    # KPI summary cards
    curr_metrics = calculate_overview_metrics(filtered_df)
    prev_metrics = calculate_overview_metrics(filtered_prev_df)

    kpi_cols = st.columns(4)
    with kpi_cols[0]:
        render_kpi_card(
            "Total users",
            f"{curr_metrics['total_users']:,}",
            calculate_change_pct(
                curr_metrics["total_users"], prev_metrics["total_users"]
            ),
        )
    with kpi_cols[1]:
        render_kpi_card(
            "Avg completion rate",
            f"{curr_metrics['avg_completion_rate']:.1%}",
            calculate_change_pct(
                curr_metrics["avg_completion_rate"],
                prev_metrics["avg_completion_rate"],
            ),
        )
    with kpi_cols[2]:
        render_kpi_card(
            "Finished exercise",
            f"{curr_metrics['total_finished']:,}",
            calculate_change_pct(
                curr_metrics["total_finished"], prev_metrics["total_finished"]
            ),
        )
    with kpi_cols[3]:
        render_kpi_card(
            "Submitted email",
            f"{curr_metrics['total_email']:,}",
            calculate_change_pct(
                curr_metrics["total_email"], prev_metrics["total_email"]
            ),
        )

    # Color legend
    render_color_legend()

    # Tool cards grid
    tool_summary = get_tool_summary(filtered_df)

    if tool_summary.empty:
        st.info("No tool data available for the selected filters.")
    else:
        # Compute previous period change for each tool
        prev_summary = get_tool_summary(filtered_prev_df)
        prev_rates = {}
        if not prev_summary.empty:
            prev_rates = dict(
                zip(prev_summary["toolKey"], prev_summary["completion_rate"])
            )

        # Pagination
        items_per_page = 8
        total_tools = len(tool_summary)

        selected_page = render_pagination(
            total_tools,
            items_per_page,
            st.session_state.current_page,
        )
        if selected_page != st.session_state.current_page:
            st.session_state.current_page = selected_page
            st.rerun()

        start_idx = st.session_state.current_page * items_per_page
        end_idx = min(start_idx + items_per_page, total_tools)
        page_tools = tool_summary.iloc[start_idx:end_idx]

        # Render 4-column grid
        cols = st.columns(4)
        for i, (_, row) in enumerate(page_tools.iterrows()):
            with cols[i % 4]:
                prev_rate = prev_rates.get(row["toolKey"])
                change = calculate_change_pct(
                    row["completion_rate"], prev_rate
                ) if prev_rate is not None else None

                sparkline = get_sparkline_data(filtered_df, row["toolKey"])

                clicked = render_tool_card(
                    tool_name=row["toolName"],
                    finished_count=row["finished_count"],
                    completion_rate=row["completion_rate"],
                    change_pct=change,
                    sparkline_data=sparkline,
                    color=row["color"],
                    tool_key=row["toolKey"],
                )
                if clicked:
                    _navigate_to_detail(row["toolKey"])
                    st.rerun()
