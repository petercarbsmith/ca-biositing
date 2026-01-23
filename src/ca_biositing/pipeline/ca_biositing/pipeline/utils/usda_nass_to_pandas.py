"""
USDA NASS Census and Survey Data Extraction

This module provides a function to extract agricultural data from the USDA NASS
Quick Stats API and convert it into a pandas DataFrame.

The USDA QuickStats API documentation:
https://quickstats.nass.usda.gov/api

API Key Setup:
1. Go to https://quickstats.nass.usda.gov/api and request a free API key
2. Set environment variable: USDA_NASS_API_KEY=your_key_here
"""

import os
import requests
import pandas as pd
from typing import Optional, List
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Configuration
BASE_URL = "https://quickstats.nass.usda.gov/api/api_GET"
TIMEOUT = 30
MAX_RETRIES = 3


def _get_session_with_retries():
    """
    Create a requests session with retry strategy for resilience.

    Returns:
        requests.Session: Session with retry strategy configured
    """
    session = requests.Session()
    retry_strategy = Retry(
        total=MAX_RETRIES,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def usda_nass_to_df(
    api_key: str,
    state: str = "CA",
    year: Optional[int] = None,
    commodity: Optional[str] = None,
    commodity_ids: Optional[List[int]] = None,
    **kwargs
) -> Optional[pd.DataFrame]:
    """
    Fetch agricultural data from USDA NASS QuickStats API.

    This function queries the USDA NASS API for agricultural census and survey data.
    It supports filtering by state, year, and commodity (by name or by ID).

    Args:
        api_key (str): Your USDA NASS API key (get free key from https://quickstats.nass.usda.gov/api)
        state (str): State code, e.g., "CA" for California. Default: "CA"
        year (Optional[int]): Filter by specific year (e.g., 2023). Default: None (all years)
        commodity (Optional[str]): Filter by commodity name (e.g., "CORN", "ALMONDS").
                                  Default: None (all commodities)
        commodity_ids (Optional[List[int]]): List of commodity IDs from resource_usda_commodity_map.
                                            When provided, takes precedence over commodity parameter.
                                            Default: None
        **kwargs: Additional parameters to pass to USDA API (e.g., data_item, agg_level_desc)

    Returns:
        Optional[pd.DataFrame]: DataFrame containing USDA data, or None if query fails

    Raises:
        ValueError: If api_key is empty

    Example:
        >>> df = usda_nass_to_df(
        ...     api_key="your_key",
        ...     state="CA",
        ...     year=2023,
        ...     commodity="CORN"
        ... )
    """

    if not api_key:
        print("Error: USDA_NASS_API_KEY is not set. Get a free key at https://quickstats.nass.usda.gov/api")
        return None

    # Base parameters for all requests
    base_params = {
        "key": api_key,
        "state_alpha": state,
        "format": "JSON",
    }

    # Add optional filters
    if year is not None:
        base_params["year"] = year

    # Add any additional kwargs
    base_params.update(kwargs)

    session = _get_session_with_retries()
    all_dfs = []

    try:
        # Handle commodity_ids query (database-driven approach)
        if commodity_ids is not None:
            if not commodity_ids:
                print("Warning: commodity_ids list is empty. No data to fetch.")
                return pd.DataFrame()

            print(f"Querying USDA API for {len(commodity_ids)} commodities...")

            for idx, comm_id in enumerate(commodity_ids, 1):
                print(f"  [{idx}/{len(commodity_ids)}] Fetching commodity ID {comm_id}...")

                # Create params for this commodity
                params = base_params.copy()
                params["commodity_code"] = comm_id

                try:
                    response = session.get(BASE_URL, params=params, timeout=TIMEOUT)
                    response.raise_for_status()

                    data = response.json()

                    # Check for API errors
                    if isinstance(data, dict) and "error" in data:
                        print(f"    USDA API Error: {data['error']}")
                        continue

                    # Check if data is a list (successful query)
                    if isinstance(data, list) and len(data) > 0:
                        df = pd.DataFrame(data)
                        all_dfs.append(df)
                        print(f"    ✓ Retrieved {len(df)} records for commodity {comm_id}")
                    else:
                        print(f"    No data returned for commodity {comm_id}")

                    # Rate limiting (USDA API courtesy)
                    time.sleep(0.5)

                except requests.exceptions.RequestException as e:
                    print(f"    Request failed for commodity {comm_id}: {e}")
                    continue

        # Handle commodity name query (fallback)
        elif commodity is not None:
            print(f"Querying USDA API for commodity: {commodity}")
            params = base_params.copy()
            params["commodity_desc"] = commodity

            try:
                response = session.get(BASE_URL, params=params, timeout=TIMEOUT)
                response.raise_for_status()

                data = response.json()

                if isinstance(data, dict) and "error" in data:
                    print(f"USDA API Error: {data['error']}")
                    return None

                if isinstance(data, list) and len(data) > 0:
                    df = pd.DataFrame(data)
                    all_dfs.append(df)
                    print(f"✓ Retrieved {len(df)} records for commodity {commodity}")
                else:
                    print(f"No data returned for commodity {commodity}")

            except requests.exceptions.RequestException as e:
                print(f"Request failed: {e}")
                return None

        # Query all data (no commodity filter)
        else:
            print("Querying USDA API for all commodities in state...")
            try:
                response = session.get(BASE_URL, params=base_params, timeout=TIMEOUT)
                response.raise_for_status()

                data = response.json()

                if isinstance(data, dict) and "error" in data:
                    print(f"USDA API Error: {data['error']}")
                    return None

                if isinstance(data, list) and len(data) > 0:
                    df = pd.DataFrame(data)
                    all_dfs.append(df)
                    print(f"✓ Retrieved {len(df)} total records")
                else:
                    print("No data returned from API")

            except requests.exceptions.RequestException as e:
                print(f"Request failed: {e}")
                return None

        # Combine all DataFrames if multiple queries were made
        if len(all_dfs) == 0:
            print("No data retrieved from USDA API.")
            return pd.DataFrame()

        if len(all_dfs) == 1:
            result_df = all_dfs[0]
        else:
            result_df = pd.concat(all_dfs, ignore_index=True)
            print(f"✓ Combined {len(all_dfs)} queries into {len(result_df)} total records")

        return result_df

    except Exception as e:
        print(f"Unexpected error fetching USDA data: {e}")
        return None
    finally:
        session.close()


if __name__ == "__main__":
    # Example usage for testing
    api_key = os.getenv("USDA_NASS_API_KEY", "")

    if not api_key:
        print("To test this module, set USDA_NASS_API_KEY environment variable")
        print("Get a free key at: https://quickstats.nass.usda.gov/api")
    else:
        # Test query for a single commodity
        print("=== Testing USDA API with commodity name ===")
        df = usda_nass_to_df(api_key=api_key, state="CA", year=2023, commodity="CORN")
        if df is not None:
            print(f"\nResult shape: {df.shape}")
            print(f"Columns: {df.columns.tolist()}")
            print(f"\nFirst few rows:")
            print(df.head())
