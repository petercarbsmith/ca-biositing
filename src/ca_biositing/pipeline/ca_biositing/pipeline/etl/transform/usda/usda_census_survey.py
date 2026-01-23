"""
USDA Census/Survey Data Transform

Transforms raw USDA data into clean, normalized records ready for loading.

This task:
1. Validates required columns
2. Cleans and standardizes values
3. Maps external codes to internal IDs
4. Prepares data for UsdaCensusRecord table
"""

from typing import Optional, Dict
import pandas as pd
from prefect import task, get_run_logger


@task
def transform(data_sources: Dict[str, pd.DataFrame]) -> Optional[pd.DataFrame]:
    """
    Transform raw USDA data into clean records.

    Args:
        data_sources: Dictionary with 'usda_census_survey' key containing raw USDA data

    Returns:
        DataFrame ready for loading into usda_census_record table, or None on error
    """
    logger = get_run_logger()
    logger.info("Transforming USDA census/survey data...")

    # Get the raw data
    if 'usda_census_survey' not in data_sources:
        logger.error("Required source 'usda_census_survey' not found in data_sources")
        return None

    raw_df = data_sources['usda_census_survey']

    if raw_df is None or len(raw_df) == 0:
        logger.warning("No data to transform (raw dataframe is empty or None)")
        return pd.DataFrame()

    logger.info(f"Starting with {len(raw_df)} raw records")

    try:
        # Make a copy to avoid modifying the original
        df = raw_df.copy()

        # Step 1: Validate required columns from USDA API
        required_cols = ['state_alpha', 'county_code', 'commodity_code', 'year', 'value']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.warning(f"Missing expected columns: {missing_cols}")
            logger.info(f"Available columns: {df.columns.tolist()}")

        # Step 2: Standardize column names (USDA API returns various formats)
        df.columns = df.columns.str.lower().str.strip()

        # Step 3: Data cleaning
        # - Remove rows with missing critical values
        df = df.dropna(subset=['state_alpha', 'commodity_code'])
        logger.info(f"After removing nulls: {len(df)} records")

        # - Standardize state codes (ensure uppercase)
        if 'state_alpha' in df.columns:
            df['state_alpha'] = df['state_alpha'].str.upper()

        # - Convert codes to integers where appropriate
        if 'county_code' in df.columns:
            df['county_code'] = pd.to_numeric(df['county_code'], errors='coerce')
        if 'commodity_code' in df.columns:
            df['commodity_code'] = pd.to_numeric(df['commodity_code'], errors='coerce')
        if 'year' in df.columns:
            df['year'] = pd.to_numeric(df['year'], errors='coerce')

        # - Handle value column (numeric with special cases)
        if 'value' in df.columns:
            # Remove any commas that might be in values
            df['value'] = df['value'].astype(str).str.replace(',', '')
            df['value'] = pd.to_numeric(df['value'], errors='coerce')

        # Step 4: Create geoid (standard geographic identifier)
        # Format: "SSCCC" where SS = state FIPS, CCC = county FIPS
        # For now, we'll use a simplified version
        if 'county_code' in df.columns:
            df['geoid'] = df['state_alpha'] + '_' + df['county_code'].astype(str)

        # Step 5: Select columns for loading
        output_cols = ['geoid', 'commodity_code', 'year', 'value']

        # Add optional columns if they exist
        optional_cols = ['source_reference', 'notes', 'data_source']
        for col in optional_cols:
            if col in df.columns:
                output_cols.append(col)

        # Filter to only available columns
        output_cols = [col for col in output_cols if col in df.columns]
        df_clean = df[output_cols].copy()

        # Step 6: Remove duplicates
        initial_count = len(df_clean)
        df_clean = df_clean.drop_duplicates()
        if len(df_clean) < initial_count:
            logger.info(f"Removed {initial_count - len(df_clean)} duplicate records")

        logger.info(f"Transform complete: {len(df_clean)} clean records ready for load")
        return df_clean

    except Exception as e:
        logger.error(f"Transform failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


if __name__ == "__main__":
    # Example for local testing
    import sys
    sys.path.insert(0, 'src/ca_biositing/pipeline')

    # Create sample data
    sample_data = {
        'usda_census_survey': pd.DataFrame({
            'state_alpha': ['CA', 'CA', 'CA'],
            'county_code': ['001', '003', '005'],
            'commodity_code': [26, 26, 26],
            'year': [2023, 2023, 2023],
            'value': ['1,000,000', '2,500,000', '1,200,000'],
            'source_reference': ['NASS', 'NASS', 'NASS']
        })
    }

    df_result = transform(sample_data)
    if df_result is not None:
        print(f"Transform test passed: {len(df_result)} records")
        print(df_result.head())
    else:
        print("Transform test failed")
