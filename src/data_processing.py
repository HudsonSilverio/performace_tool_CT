"""Data transformation and funnel calculation functions."""

from datetime import date, timedelta

import pandas as pd

from tools_config import TOOLS_MAP


def normalize_page_paths(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure all pagePath values start with '/'.

    Args:
        df: DataFrame with a 'pagePath' column.

    Returns:
        DataFrame with normalized pagePath values.
    """
    if df.empty or "pagePath" not in df.columns:
        return df
    df = df.copy()
    df["pagePath"] = df["pagePath"].apply(
        lambda p: p if p.startswith("/") else f"/{p}"
    )
    return df


def filter_known_tools(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only rows whose pagePath matches a known tool.

    Args:
        df: DataFrame with a 'pagePath' column.

    Returns:
        Filtered DataFrame containing only known tool paths.
    """
    if df.empty or "pagePath" not in df.columns:
        return df

    known_paths = set(TOOLS_MAP.keys())

    def _matches_known_path(page_path: str) -> bool:
        if page_path in known_paths:
            return True
        for known in known_paths:
            if page_path.endswith(known) or page_path.endswith(known.rstrip("/")):
                return True
        return False

    mask = df["pagePath"].apply(_matches_known_path)
    return df[mask].copy()


def _resolve_tool_path(page_path: str) -> str:
    """Resolve a pagePath to its canonical TOOLS_MAP key.

    Args:
        page_path: Raw pagePath value from GA4.

    Returns:
        The matching TOOLS_MAP key, or the original path if no match.
    """
    if page_path in TOOLS_MAP:
        return page_path
    for known in TOOLS_MAP:
        if page_path.endswith(known) or page_path.endswith(known.rstrip("/")):
            return known
    return page_path


def add_tool_name_column(df: pd.DataFrame) -> pd.DataFrame:
    """Add a 'toolName' column based on pagePath.

    Args:
        df: DataFrame with a 'pagePath' column.

    Returns:
        DataFrame with an added 'toolName' column.
    """
    if df.empty:
        return df
    df = df.copy()
    df["toolKey"] = df["pagePath"].apply(_resolve_tool_path)
    df["toolName"] = df["toolKey"].map(TOOLS_MAP)
    return df


def apply_filters(
    df: pd.DataFrame,
    filters: dict[str, list[str]],
) -> pd.DataFrame:
    """Apply sidebar filter selections to the DataFrame.

    Args:
        df: Full DataFrame.
        filters: Dict mapping column names to selected values.
                 Empty list means no filter (show all).

    Returns:
        Filtered DataFrame.
    """
    if df.empty:
        return df
    filtered = df.copy()
    for column, values in filters.items():
        if values and column in filtered.columns:
            filtered = filtered[filtered[column].isin(values)]
    return filtered


def get_filter_options(df: pd.DataFrame, dimension: str) -> list[str]:
    """Get unique values for a filter dimension.

    Args:
        df: DataFrame containing the dimension column.
        dimension: Column name to extract unique values from.

    Returns:
        Sorted list of unique values, with '(not set)' displayed as 'Not set'.
    """
    if df.empty or dimension not in df.columns:
        return []
    values = df[dimension].unique().tolist()
    values = [v if v != "(not set)" else "Not set" for v in values]
    return sorted(values)


def calculate_completion_rate(finished: int, viewed: int) -> float:
    """Calculate completion rate with safe division.

    Args:
        finished: Count of 'Finished Exercise' events.
        viewed: Count of 'Viewed Privacy Policy' events.

    Returns:
        Completion rate as a float (0.0 to 1.0).
    """
    if viewed == 0:
        return 0.0
    return finished / viewed


def calculate_change_pct(current: float, previous: float) -> float | None:
    """Calculate percentage change between periods.

    Args:
        current: Current period value.
        previous: Previous period value.

    Returns:
        Percentage change, or None if previous is 0.
    """
    if previous == 0:
        return None
    return ((current - previous) / previous) * 100


def calculate_previous_period(
    start_date: date,
    end_date: date,
) -> tuple[date, date]:
    """Calculate the previous period dates for comparison.

    Args:
        start_date: Current period start date.
        end_date: Current period end date.

    Returns:
        Tuple of (previous_start, previous_end).
    """
    selected_days = (end_date - start_date).days + 1
    previous_end = start_date - timedelta(days=1)
    previous_start = start_date - timedelta(days=selected_days)
    return previous_start, previous_end


def get_performance_color(completion_rate: float) -> str:
    """Get card border color based on completion rate threshold.

    Args:
        completion_rate: Completion rate as a float (0.0 to 1.0).

    Returns:
        Hex color string.
    """
    if completion_rate >= 0.10:
        return "#1D9E75"
    elif completion_rate >= 0.05:
        return "#BA7517"
    else:
        return "#E24B4A"


def get_event_count(
    df: pd.DataFrame,
    event_name: str,
    tool_key: str | None = None,
) -> int:
    """Get total event count for a specific event, optionally filtered by tool.

    Args:
        df: DataFrame with 'eventName', 'eventCount', and optionally 'toolKey'.
        event_name: The event name to count.
        tool_key: Optional tool path to filter by.

    Returns:
        Total event count.
    """
    if df.empty:
        return 0
    mask = df["eventName"] == event_name
    if tool_key is not None and "toolKey" in df.columns:
        mask = mask & (df["toolKey"] == tool_key)
    return int(df.loc[mask, "eventCount"].sum())


def calculate_funnel_metrics(
    df: pd.DataFrame,
    tool_key: str,
) -> list[dict[str, str | int | float]]:
    """Calculate funnel step metrics for a specific tool.

    Args:
        df: Processed DataFrame with 'toolKey' and 'eventName' columns.
        tool_key: The tool path key.

    Returns:
        List of dicts with keys: step_name, count, percentage, dropoff.
    """
    funnel_steps = [
        "Viewed Privacy Policy",
        "Accepted Privacy Policy",
        "Reached Email Ask",
        "Submitted Email",
        "Finished Exercise",
    ]

    results: list[dict[str, str | int | float]] = []
    first_step_count = get_event_count(df, funnel_steps[0], tool_key)

    for i, step in enumerate(funnel_steps):
        count = get_event_count(df, step, tool_key)
        percentage = (count / first_step_count * 100) if first_step_count > 0 else 0.0

        if i == 0:
            dropoff = 0.0
        else:
            prev_count = results[i - 1]["count"]
            if prev_count > 0:
                dropoff = (1 - count / prev_count) * 100
            else:
                dropoff = 0.0

        results.append({
            "step_name": step,
            "count": count,
            "percentage": percentage,
            "dropoff": dropoff,
        })

    return results


def calculate_overview_metrics(
    df: pd.DataFrame,
) -> dict[str, int | float]:
    """Calculate aggregate KPI metrics across all tools.

    Args:
        df: Processed DataFrame.

    Returns:
        Dict with keys: total_users, avg_completion_rate,
        total_finished, total_email.
    """
    if df.empty:
        return {
            "total_users": 0,
            "avg_completion_rate": 0.0,
            "total_finished": 0,
            "total_email": 0,
        }

    total_finished = get_event_count(df, "Finished Exercise")
    total_email = get_event_count(df, "Submitted Email")
    total_viewed = get_event_count(df, "Viewed Privacy Policy")

    # Per-tool completion rates for averaging
    if "toolKey" in df.columns:
        tool_keys = df["toolKey"].unique()
        rates: list[float] = []
        for tk in tool_keys:
            viewed = get_event_count(df, "Viewed Privacy Policy", tk)
            finished = get_event_count(df, "Finished Exercise", tk)
            if viewed > 0:
                rates.append(finished / viewed)
        avg_completion = sum(rates) / len(rates) if rates else 0.0
    else:
        avg_completion = calculate_completion_rate(total_finished, total_viewed)

    return {
        "total_users": total_viewed,
        "avg_completion_rate": avg_completion,
        "total_finished": total_finished,
        "total_email": total_email,
    }


def get_tool_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Generate summary metrics for each tool (for the overview grid).

    Args:
        df: Processed DataFrame with 'toolKey', 'toolName', 'eventName',
            'eventCount' columns.

    Returns:
        DataFrame with columns: toolKey, toolName, finished_count,
        viewed_count, completion_rate, color, sorted by completion_rate desc.
    """
    if df.empty:
        return pd.DataFrame()

    tool_keys = df["toolKey"].unique()
    summaries: list[dict] = []

    for tk in tool_keys:
        tool_name = TOOLS_MAP.get(tk, tk)
        viewed = get_event_count(df, "Viewed Privacy Policy", tk)
        finished = get_event_count(df, "Finished Exercise", tk)
        comp_rate = calculate_completion_rate(finished, viewed)

        summaries.append({
            "toolKey": tk,
            "toolName": tool_name,
            "finished_count": finished,
            "viewed_count": viewed,
            "completion_rate": comp_rate,
            "color": get_performance_color(comp_rate),
        })

    summary_df = pd.DataFrame(summaries)
    summary_df = summary_df.sort_values("completion_rate", ascending=False)
    return summary_df.reset_index(drop=True)


def get_sparkline_data(
    df: pd.DataFrame,
    tool_key: str,
) -> list[int]:
    """Get daily 'Finished Exercise' counts for a tool (for sparkline chart).

    Args:
        df: DataFrame with 'date', 'eventName', 'toolKey', 'eventCount'.
        tool_key: The tool path key.

    Returns:
        List of daily event counts sorted by date.
    """
    if df.empty:
        return []

    mask = (
        (df["eventName"] == "Finished Exercise")
        & (df["toolKey"] == tool_key)
    )
    tool_data = df.loc[mask].copy()

    if tool_data.empty:
        return []

    daily = (
        tool_data.groupby("date")["eventCount"]
        .sum()
        .sort_index()
        .tolist()
    )
    return daily


def process_raw_data(df: pd.DataFrame) -> pd.DataFrame:
    """Full processing pipeline for raw GA4 data.

    Args:
        df: Raw DataFrame from GA4 API.

    Returns:
        Processed DataFrame with normalized paths, known tools only,
        and tool name column added.
    """
    if df.empty:
        return df
    df = normalize_page_paths(df)
    df = filter_known_tools(df)
    df = add_tool_name_column(df)
    return df
