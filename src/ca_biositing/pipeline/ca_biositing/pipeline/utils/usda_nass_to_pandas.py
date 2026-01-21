"""
USDA NASS Quick Stats API Data Extraction
---

This module provides utilities to extract agricultural data directly from the
USDA NASS Quick Stats API.

The USDA NASS Quick Stats API provides access to:
- Census data (every 5 years)
- Survey data (annual estimates)
- Agricultural statistics at state and county levels

For more information: https://quickstats.nass.usda.gov/api
"""

import requests
import pandas as pd
from typing import Optional, Dict, Any, List


def usda_nass_to_df(
    api_key: str,
    state: str = "CA",
    year: Optional[int] = None,
    commodity: Optional[str] = None,
    commodity_ids: Optional[List[int]] = None,
    **kwargs
) -> Optional[pd.DataFrame]:
    """
    Fetches agricultural data from the USDA NASS Quick Stats API and returns
    it as a pandas DataFrame.

    This function queries the USDA NASS Quick Stats API for agricultural
    statistics. It handles authentication, request construction, error handling,
    and JSON-to-DataFrame conversion.

    Args:
        api_key: Your USDA NASS API key (get one at https://quickstats.nass.usda.gov/api)
        state: State code (default: "CA" for California). Use USDA state abbreviations.
        year: Year to query (optional). If None, returns all available years.
        commodity: Commodity description (optional). Examples: "CORN", "ALMONDS", "WHEAT"
        **kwargs: Additional USDA API parameters. Examples:
            - data_item: Specific measurement (e.g., "PRODUCTION", "AREA HARVESTED")
            - agg_level_desc: Aggregation level (e.g., "STATE", "COUNTY")

    Returns:
        A pandas DataFrame containing the API response data, or None if an error occurs.

    Example:
        >>> api_key = "your_api_key_here"
        >>> df = usda_nass_to_df(api_key, state="CA", year=2023, commodity="CORN")
        >>> if df is not None:
        ...     print(f"Retrieved {len(df)} records")
        ... else:
        ...     print("Failed to fetch data")
    """

    # USDA API endpoint
    BASE_URL = "https://quickstats.nass.usda.gov/api/api_GET"

    # Build the query parameters dictionary
    # Always include the state filter (we want California data)
    params = {
        "key": api_key,
        "state_alpha": state,
        "format": "JSON",  # Request JSON format
    }

     # NEW: Handle commodity_ids parameter
    if commodity_ids is not None:
        logger.info(f"Querying {len(commodity_ids)} commodities by ID...")
        all_dfs = []

        for comm_id in commodity_ids:
            query_params = params.copy()
            query_params["commodity_code"] = comm_id  # API parameter for ID

            try:
                response = requests.get(BASE_URL, params=query_params, timeout=30)
                response.raise_for_status()
                data = response.json()

                if data and not isinstance(data, dict):
                    df = pd.DataFrame(data)
                    all_dfs.append(df)
                    logger.info(f"  Commodity {comm_id}: {len(df)} records")
            except Exception as e:
                logger.error(f"  Error querying commodity {comm_id}: {e}")

        if all_dfs:
            result = pd.concat(all_dfs, ignore_index=True)
            logger.info(f"Total: {len(result)} records from {len(commodity_ids)} commodities")
            return result
        else:
            logger.warning("No data returned for any commodity")
            return pd.DataFrame()

    # EXISTING CODE: Fall back to commodity name if IDs not provided
    if commodity is not None:
        params["commodity_desc"] = commodity

    # Add optional filters if provided
    if year is not None:
        params["year"] = year

    if commodity is not None:
        params["commodity_desc"] = commodity

    # Add any additional parameters passed by the caller
    params.update(kwargs)

    try:
        # Make the HTTP GET request to USDA
        # This is synchronous - it waits for the response before continuing
        print(f"Querying USDA NASS API for {state} data...")
        response = requests.get(BASE_URL, params=params, timeout=30)

        # Check if the request was successful (HTTP status 200)
        response.raise_for_status()

        # Parse the JSON response
        data = response.json()

        # Check if the API returned an error message
        # USDA API returns {'error': 'message'} on failure
        if isinstance(data, dict) and "error" in data:
            print(f"USDA API Error: {data['error']}")
            return None

        # If data is empty, return empty DataFrame (not an error)
        if not data or len(data) == 0:
            print(f"No records found for the specified query.")
            return pd.DataFrame()

        # Convert JSON array to pandas DataFrame
        # This creates a table with columns matching the JSON keys
        df = pd.DataFrame(data)

        print(f"Successfully retrieved {len(df)} records from USDA NASS API")
        return df

    except requests.exceptions.Timeout:
        print("Error: Request to USDA API timed out (exceeded 30 seconds)")
        return None

    except requests.exceptions.ConnectionError:
        print("Error: Failed to connect to USDA API. Check your internet connection.")
        return None

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e.response.status_code} - {e.response.reason}")
        print(f"Response: {e.response.text}")
        return None

    except ValueError as e:
        print(f"Error parsing JSON response from USDA API: {e}")
        return None

    except Exception as e:
        print(f"Unexpected error while querying USDA NASS API: {e}")
        return None


def get_available_parameters(api_key: str) -> Dict[str, Any]:
    """
    Fetches the list of available parameters for the USDA NASS API.

    This helper function retrieves metadata about what commodities, data items,
    and other parameters are available in the API. Useful for discovering what
    data you can query.

    Args:
        api_key: Your USDA NASS API key

    Returns:
        A dictionary containing available commodities, data items, and states,
        or an empty dictionary if the request fails.

    Note:
        This function requires making multiple API calls and may take several
        seconds to complete. Cache the results if calling frequently.
    """
    BASE_URL = "https://quickstats.nass.usda.gov/api/get_param_values"

    available_params = {}

    # Common parameters to fetch
    param_names = ["commodity_desc", "state_alpha", "data_item", "year"]

    try:
        for param in param_names:
            print(f"Fetching available values for {param}...")
            response = requests.get(
                BASE_URL,
                params={"key": api_key, "param": param},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            if "results" in data:
                available_params[param] = data["results"]

    except Exception as e:
        print(f"Error fetching parameter values: {e}")

    return available_params
