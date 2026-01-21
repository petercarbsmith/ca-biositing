"""
USDA Census and Survey Data Extraction
---

This module extracts agricultural census and survey data from the USDA NASS
Quick Stats API for California.

Data includes:
- Census data (every 5 years): Complete agricultural census
- Survey data (annual): Preliminary and final agricultural estimates

The USDA API provides access to decades of historical data across many
commodities and regions.

For more information: https://quickstats.nass.usda.gov/api
"""

from typing import Optional
import os
import pandas as pd
from prefect import task, get_run_logger

# Use absolute imports that work both locally and in Docker
try:
    # Try absolute import first (works in Docker)
    from ca_biositing.pipeline.utils.usda_nass_to_pandas import usda_nass_to_df
    from ca_biositing.pipeline.utils.commodity_mapper import get_mapped_commodity_ids
except ImportError:
    # Fallback for local testing
    from src.ca_biositing.pipeline.ca_biositing.pipeline.utils.usda_nass_to_pandas import usda_nass_to_df
    from src.ca_biositing.pipeline.ca_biositing.pipeline.utils.commodity_mapper import get_mapped_commodity_ids

# --- CONFIGURATION ---
# USDA API Key - loaded from environment variable
# To set this, add to resources/docker/.env:
#   USDA_NASS_API_KEY=your_api_key_here
# Get your free API key at: https://quickstats.nass.usda.gov/api
USDA_API_KEY = os.getenv("USDA_NASS_API_KEY", "")

# State code to query (using USDA state abbreviation)
# CA = California
STATE = "CA"

# Optional: Filter by specific year. Set to None for all available years.
YEAR = None

# Optional: Filter by commodity (e.g., "CORN", "ALMONDS", "WHEAT")
# Leave as None to get all commodities
COMMODITY = None


@task
def extract() -> Optional[pd.DataFrame]:
    """
    Extracts USDA data ONLY for commodities mapped in resource_usda_commodity_map.

    This allows adding new crops by updating the database, no code changes needed.
    """
    logger = get_run_logger()

    # Get commodity IDs from database
    commodity_ids = get_mapped_commodity_ids()

    if not commodity_ids:
        logger.warning(
            "No commodity mappings found in resource_usda_commodity_map. "
            "Please run bootstrap_usda_commodities flow to populate commodities, "
            "then create mappings for your crops."
        )
        return None

    logger.info(f"Extracting USDA data for {len(commodity_ids)} commodities...")

    # Call utility with commodity IDs (not names)
    raw_df = usda_nass_to_df(
        api_key=USDA_API_KEY,
        state=STATE,
        year=YEAR,
        commodity_ids=commodity_ids  # ← Database-driven!
    )

    if raw_df is None:
        logger.error("Failed to extract data from USDA API. Aborting.")
        return None

    logger.info(f"Successfully extracted {len(raw_df)} records from USDA NASS API.")
    return raw_df
