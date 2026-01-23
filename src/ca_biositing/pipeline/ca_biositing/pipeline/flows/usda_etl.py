"""
USDA Census/Survey Data ETL Flow

Complete ETL pipeline for importing USDA agricultural data:
1. Extract: Query USDA API for mapped commodities
2. Transform: Clean and normalize raw data
3. Load: Insert into database

This flow can be triggered via Prefect UI or CLI:
    prefect deployment build usda_etl.py:usda_etl_flow
    prefect deployment apply usda_etl_flow-deployment.yaml
    prefect deployment run "usda-etl-flow"
"""

from prefect import flow
from ca_biositing.pipeline.etl.extract.usda_census_survey import extract
from ca_biositing.pipeline.etl.transform.usda.usda_census_survey import transform
from ca_biositing.pipeline.etl.load.usda.usda_census_survey import load


@flow(name="USDA Census Survey ETL", log_prints=True)
def usda_etl_flow():
    """
    Complete ETL flow for USDA agricultural data import.

    Steps:
    1. Extract: Queries USDA API for all mapped commodities in California
    2. Transform: Cleans and normalizes the data
    3. Load: Inserts into usda_census_record table

    The flow reads commodity mappings from resource_usda_commodity_map table,
    so adding new crops requires only database changes, not code changes.
    """
    print("=" * 70)
    print("USDA Census/Survey Data ETL Flow Started")
    print("=" * 70)

    # Step 1: Extract
    print("\n[Step 1] Extracting USDA data...")
    raw_data = extract()

    if raw_data is None:
        print("✗ Extract failed. Aborting flow.")
        return False

    print(f"✓ Extract complete: {len(raw_data)} records retrieved")

    # Step 2: Transform
    print("\n[Step 2] Transforming raw data...")
    data_sources = {"usda_census_survey": raw_data}
    cleaned_data = transform(data_sources)

    if cleaned_data is None:
        print("✗ Transform failed. Aborting flow.")
        return False

    print(f"✓ Transform complete: {len(cleaned_data)} records cleaned")

    # Step 3: Load
    print("\n[Step 3] Loading data into database...")
    success = load(cleaned_data)

    if success:
        print(f"✓ Load complete: {len(cleaned_data)} records loaded")
    else:
        print("✗ Load failed.")
        return False

    print("\n" + "=" * 70)
    print("✓ USDA ETL Flow Completed Successfully")
    print("=" * 70)

    return True


if __name__ == "__main__":
    # Can run directly: python usda_etl.py
    result = usda_etl_flow()
    if result:
        print("\n✓ Flow execution successful!")
    else:
        print("\n✗ Flow execution failed!")
