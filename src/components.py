"""Reusable UI components for the dashboard."""

import base64
import os
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st


def _load_logo_base64() -> str | None:
    """Load logo.png as base64 string for embedding in HTML.

    Returns:
        Base64-encoded string, or None if file not found.
    """
    logo_path = Path(__file__).parent.parent / "assets" / "logo.png"
    if not logo_path.exists():
        return None
    with open(logo_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def render_header(active_page: str = "overview") -> None:
    """Render the dashboard header bar.

    Args:
        active_page: Currently active page ('overview' or 'detail').
    """
    logo_b64 = _load_logo_base64()
    logo_html = ""
    if logo_b64:
        logo_html = (
            f'<img src="data:image/png;base64,{logo_b64}" '
            f'style="height:32px;margin-right:12px;" />'
        )

    overview_style = "font-weight:600;" if active_page == "overview" else ""
    detail_style = "font-weight:600;" if active_page == "detail" else ""
    overview_underline = (
        "border-bottom:2px solid #fff;padding-bottom:4px;"
        if active_page == "overview" else ""
    )
    detail_underline = (
        "border-bottom:2px solid #fff;padding-bottom:4px;"
        if active_page == "detail" else ""
    )

    st.markdown(
        f"""
        <div style="
            background-color:#1A73E8;
            padding:12px 24px;
            display:flex;
            align-items:center;
            justify-content:space-between;
            border-radius:8px;
            margin-bottom:20px;
        ">
            <div style="display:flex;align-items:center;">
                {logo_html}
                <span style="color:#fff;font-size:20px;font-weight:600;">
                    Tools performance dashboard
                </span>
            </div>
            <div style="display:flex;gap:20px;">
                <span style="color:#fff;font-size:14px;{overview_style}{overview_underline}">
                    Overview
                </span>
                <span style="color:#fff;font-size:14px;{detail_style}{detail_underline}">
                    Tool detail
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_card(
    title: str,
    value: str,
    change_pct: float | None = None,
    prefix: str = "",
    suffix: str = "",
) -> None:
    """Render a KPI summary card.

    Args:
        title: Card title label.
        value: Main KPI value to display.
        change_pct: Percentage change vs previous period (None = N/A).
        prefix: Text before the value (e.g., currency symbol).
        suffix: Text after the value (e.g., '%').
    """
    if change_pct is not None:
        arrow = "&#9650;" if change_pct >= 0 else "&#9660;"
        color = "#1D9E75" if change_pct >= 0 else "#E24B4A"
        change_html = (
            f'<span style="font-size:11px;color:{color};">'
            f'{arrow} {abs(change_pct):.1f}% vs prev period</span>'
        )
    else:
        change_html = (
            '<span style="font-size:11px;color:#999;">N/A vs prev period</span>'
        )

    st.markdown(
        f"""
        <div style="
            background:#fff;
            border:1px solid #E0E0E0;
            border-radius:8px;
            padding:16px;
            text-align:center;
        ">
            <div style="font-size:12px;color:#999;margin-bottom:6px;">
                {title}
            </div>
            <div style="font-size:26px;font-weight:500;color:#222;margin-bottom:6px;">
                {prefix}{value}{suffix}
            </div>
            {change_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_tool_card(
    tool_name: str,
    finished_count: int,
    completion_rate: float,
    change_pct: float | None,
    sparkline_data: list[int],
    color: str,
    tool_key: str,
) -> bool:
    """Render a tool card for the overview grid.

    Args:
        tool_name: Human-readable tool name.
        finished_count: Count of Finished Exercise events.
        completion_rate: Completion rate (0.0 to 1.0).
        change_pct: Change vs previous period (None = N/A).
        sparkline_data: Daily finished counts for sparkline.
        color: Border color (hex).
        tool_key: Tool path key for navigation.

    Returns:
        True if the card was clicked.
    """
    if change_pct is not None:
        arrow = "&#9650;" if change_pct >= 0 else "&#9660;"
        trend_color = "#1D9E75" if change_pct >= 0 else "#E24B4A"
        trend_html = (
            f'<span style="font-size:11px;color:{trend_color};">'
            f'{arrow} {abs(change_pct):.1f}%</span>'
        )
    else:
        trend_html = '<span style="font-size:11px;color:#999;">N/A</span>'

    # Sparkline SVG
    sparkline_svg = _generate_sparkline_svg(sparkline_data, color)

    st.markdown(
        f"""
        <div style="
            background:#fff;
            border:1px solid #E0E0E0;
            border-left:4px solid {color};
            border-radius:8px;
            padding:14px;
            margin-bottom:8px;
            min-height:140px;
        ">
            <div style="font-size:14px;font-weight:500;color:#222;
                        margin-bottom:8px;white-space:nowrap;overflow:hidden;
                        text-overflow:ellipsis;" title="{tool_name}">
                {tool_name}
            </div>
            <div style="display:flex;align-items:baseline;gap:6px;margin-bottom:4px;">
                <span style="font-size:26px;font-weight:500;color:#222;">
                    {finished_count:,}
                </span>
                <span style="font-size:12px;color:{color};">finished</span>
            </div>
            <div style="font-size:12px;color:#999;margin-bottom:6px;">
                Completion: {completion_rate:.1%} {trend_html}
            </div>
            <div>{sparkline_svg}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    return st.button(
        "View details",
        key=f"card_{tool_key}",
        use_container_width=True,
    )


def _generate_sparkline_svg(data: list[int], color: str) -> str:
    """Generate an inline SVG sparkline.

    Args:
        data: List of values to plot.
        color: Line color (hex).

    Returns:
        SVG string.
    """
    if not data or len(data) < 2:
        return ""

    width = 180
    height = 30
    max_val = max(data) if max(data) > 0 else 1
    min_val = min(data)
    val_range = max_val - min_val if max_val != min_val else 1

    points: list[str] = []
    for i, v in enumerate(data):
        x = (i / (len(data) - 1)) * width
        y = height - ((v - min_val) / val_range) * (height - 4) - 2
        points.append(f"{x:.1f},{y:.1f}")

    polyline = " ".join(points)
    return (
        f'<svg width="{width}" height="{height}" '
        f'style="display:block;">'
        f'<polyline points="{polyline}" '
        f'fill="none" stroke="{color}" stroke-width="1.5" />'
        f"</svg>"
    )


def render_color_legend() -> None:
    """Render the color legend explaining card border colors."""
    st.markdown(
        """
        <div style="
            display:flex;
            gap:24px;
            align-items:center;
            padding:8px 0;
            margin-bottom:12px;
            font-size:12px;
            color:#666;
        ">
            <span>
                <span style="display:inline-block;width:12px;height:12px;
                             background:#1D9E75;border-radius:2px;
                             margin-right:4px;vertical-align:middle;"></span>
                Completion rate &ge; 10%
            </span>
            <span>
                <span style="display:inline-block;width:12px;height:12px;
                             background:#BA7517;border-radius:2px;
                             margin-right:4px;vertical-align:middle;"></span>
                Completion rate 5% &ndash; 10%
            </span>
            <span>
                <span style="display:inline-block;width:12px;height:12px;
                             background:#E24B4A;border-radius:2px;
                             margin-right:4px;vertical-align:middle;"></span>
                Completion rate &lt; 5%
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_funnel_chart(
    funnel_data: list[dict[str, str | int | float]],
) -> None:
    """Render the funnel visualization for a single tool.

    Args:
        funnel_data: List of dicts with step_name, count, percentage, dropoff.
    """
    if not funnel_data:
        st.info("No funnel data available for this tool.")
        return

    bar_colors = ["#1A73E8", "#3D8BE8", "#6BA8E5", "#93C1F0", "#1D9E75"]
    text_colors = ["#FFFFFF", "#FFFFFF", "#FFFFFF", "#042C53", "#FFFFFF"]

    # Reverse for bottom-to-top display in horizontal bar chart
    steps = list(reversed(funnel_data))
    colors = list(reversed(bar_colors))
    txt_colors = list(reversed(text_colors))

    first_count = funnel_data[0]["count"] if funnel_data[0]["count"] > 0 else 1

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=[s["step_name"] for s in steps],
        x=[s["count"] for s in steps],
        orientation="h",
        marker_color=colors,
        text=[
            f'  {s["count"]:,}  ({s["percentage"]:.1f}%)'
            for s in steps
        ],
        textposition="auto",
        textfont=dict(
            color=txt_colors,
            size=13,
        ),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Count: %{x:,}<br>"
            "<extra></extra>"
        ),
    ))

    fig.update_layout(
        height=300,
        margin=dict(l=0, r=40, t=10, b=10),
        xaxis=dict(visible=False),
        yaxis=dict(
            autorange="reversed",
            tickfont=dict(size=12),
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        bargap=0.25,
    )

    st.plotly_chart(fig, use_container_width=True)

    # Drop-off annotations
    for i, step in enumerate(funnel_data):
        if i > 0 and step["dropoff"] > 0:
            st.markdown(
                f"""
                <div style="text-align:center;font-size:11px;color:#E24B4A;
                            margin:-10px 0 4px 0;">
                    &#8595; {step['dropoff']:.1f}% drop-off
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_pagination(
    total_items: int,
    items_per_page: int,
    current_page: int,
) -> int:
    """Render pagination controls and return selected page.

    Args:
        total_items: Total number of items.
        items_per_page: Items to show per page.
        current_page: Currently selected page (0-indexed).

    Returns:
        Selected page number (0-indexed).
    """
    total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)

    if total_pages <= 1:
        return 0

    cols = st.columns([1, 3, 1])
    with cols[0]:
        if st.button("< Prev", disabled=current_page == 0):
            return max(0, current_page - 1)
    with cols[1]:
        page_labels = [str(i + 1) for i in range(total_pages)]
        selected_label = st.radio(
            "Page",
            page_labels,
            index=current_page,
            horizontal=True,
            label_visibility="collapsed",
        )
        selected_page = int(selected_label) - 1
    with cols[2]:
        if st.button("Next >", disabled=current_page >= total_pages - 1):
            return min(total_pages - 1, current_page + 1)

    return selected_page
