"""GA4 API client for fetching analytics data."""

import json
import logging
import time
from datetime import date

import pandas as pd
import streamlit as st
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Filter,
    FilterExpression,
    Metric,
    RunReportRequest,
    RunReportResponse,
)
from google.oauth2 import service_account

logger = logging.getLogger(__name__)

FUNNEL_EVENTS: list[str] = [
    "page_view",
    "Viewed Privacy Policy",
    "Accepted Privacy Policy",
    "Reached Email Ask",
    "Submitted Email",
    "Finished Exercise",
]

GA4_DIMENSIONS: list[str] = [
    "date",
    "pagePath",
    "eventName",
    "sessionCampaignName",
    "sessionDefaultChannelGroup",
    "deviceCategory",
    "userGender",
    "country",
    "userAgeBracket",
]

_MAX_ROWS_PER_REQUEST: int = 250000
_MAX_RETRIES: int = 3
_RETRY_BASE_DELAY: float = 2.0


def _get_ga4_client() -> BetaAnalyticsDataClient:
    """Create an authenticated GA4 client from Streamlit secrets."""
    credentials_info = json.loads(st.secrets["ga4"]["credentials"])
    credentials = service_account.Credentials.from_service_account_info(
        credentials_info,
        scopes=["https://www.googleapis.com/auth/analytics.readonly"],
    )
    return BetaAnalyticsDataClient(credentials=credentials)


def _get_property_id() -> str:
    """Get the GA4 property ID from Streamlit secrets."""
    return st.secrets["ga4"]["property_id"]


def _response_to_dataframe(response: RunReportResponse) -> pd.DataFrame:
    """Convert a GA4 RunReportResponse to a Pandas DataFrame."""
    rows_data: list[dict[str, str | int]] = []
    dimension_headers = [h.name for h in response.dimension_headers]
    metric_headers = [h.name for h in response.metric_headers]

    for row in response.rows:
        row_dict: dict[str, str | int] = {}
        for i, dim_value in enumerate(row.dimension_values):
            row_dict[dimension_headers[i]] = dim_value.value
        for i, met_value in enumerate(row.metric_values):
            row_dict[metric_headers[i]] = int(met_value.value)
        rows_data.append(row_dict)

    return pd.DataFrame(rows_data)


def _fetch_with_retry(
    client: BetaAnalyticsDataClient,
    request: RunReportRequest,
) -> RunReportResponse:
    """Execute a GA4 API request with exponential backoff retry."""
    for attempt in range(_MAX_RETRIES):
        try:
            return client.run_report(request)
        except Exception as e:
            if attempt == _MAX_RETRIES - 1:
                raise
            delay = _RETRY_BASE_DELAY * (2 ** attempt)
            logger.warning(
                "GA4 API request failed (attempt %d/%d): %s. Retrying in %.1fs",
                attempt + 1,
                _MAX_RETRIES,
                str(e),
                delay,
            )
            time.sleep(delay)
    raise RuntimeError("Unexpected: retry loop exited without return or raise")


@st.cache_data(ttl=3600, show_spinner="Loading data from Google Analytics...")
def fetch_ga4_data(
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """Fetch funnel event data from GA4 for the given date range.

    Args:
        start_date: Start date in YYYY-MM-DD format.
        end_date: End date in YYYY-MM-DD format.

    Returns:
        DataFrame with columns for each GA4 dimension plus eventCount.
    """
    try:
        client = _get_ga4_client()
        property_id = _get_property_id()
    except Exception as e:
        logger.error("Failed to initialize GA4 client: %s", str(e))
        st.error(
            "Could not connect to Google Analytics. "
            "Please check your credentials in .streamlit/secrets.toml"
        )
        return pd.DataFrame()

    request = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        dimensions=[Dimension(name=d) for d in GA4_DIMENSIONS],
        metrics=[Metric(name="eventCount")],
        dimension_filter=FilterExpression(
            filter=Filter(
                field_name="eventName",
                in_list_filter=Filter.InListFilter(values=FUNNEL_EVENTS),
            )
        ),
        limit=_MAX_ROWS_PER_REQUEST,
    )

    try:
        all_data: list[pd.DataFrame] = []
        offset = 0

        while True:
            request.offset = offset
            response = _fetch_with_retry(client, request)
            df_chunk = _response_to_dataframe(response)
            all_data.append(df_chunk)

            total_rows = response.row_count
            offset += len(response.rows)

            if offset >= total_rows:
                break

        if not all_data:
            return pd.DataFrame()

        df = pd.concat(all_data, ignore_index=True)
        return df

    except Exception as e:
        logger.error("Failed to fetch GA4 data: %s", str(e))
        st.error(
            "Error loading data from Google Analytics. "
            "Please try again or check your configuration."
        )
        return pd.DataFrame()


def fetch_data_for_period(
    start_date: date,
    end_date: date,
) -> pd.DataFrame:
    """Convenience wrapper that accepts date objects.

    Args:
        start_date: Period start date.
        end_date: Period end date.

    Returns:
        DataFrame with GA4 event data.
    """
    return fetch_ga4_data(
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
    )
