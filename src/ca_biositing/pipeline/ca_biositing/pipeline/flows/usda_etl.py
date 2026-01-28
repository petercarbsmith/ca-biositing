"""
USDA Census/Survey Data ETL Flow

Complete ETL pipeline for importing USDA agricultural data:
1. Extract: Query USDA API for mapped commodities
2. Transform: Clean and normalize raw data
3. Load: Insert into database
4. Link: Associate records with datasets for data lineage
5. Verify: Confirm all data linked correctly

This flow can be triggered via Prefect UI or CLI:
    prefect deployment build usda_etl.py:usda_etl_flow
    prefect deployment apply usda_etl_flow-deployment.yaml
    prefect deployment run "usda-etl-flow"
"""

import os
from prefect import flow, get_run_logger
from ca_biositing.pipeline.etl.extract.usda_census_survey import extract
from ca_biositing.pipeline.etl.transform.usda.usda_census_survey import transform
from ca_biositing.pipeline.etl.load.usda.usda_census_survey import load
from ca_biositing.pipeline.tasks.link_dataset_ids import (
    link_census_records_to_datasets,
    link_survey_records_to_datasets,
    link_observations_to_datasets,
    verify_dataset_linkage,
)


@flow(name="USDA Census Survey ETL", log_prints=True)
def usda_etl_flow():
    """
    Complete ETL flow for USDA agricultural data import.

    Steps:
    1. Extract: Queries USDA API for all mapped commodities in California
    2. Transform: Cleans and normalizes the data
    3. Load: Inserts into usda_census_record table
    4. Link: Associates records with datasets for data lineage
    5. Verify: Confirms all records have dataset_id populated

    The flow reads commodity mappings from resource_usda_commodity_map table,
    so adding new crops requires only database changes, not code changes.
    """
    logger = get_run_logger()
    db_url = os.getenv('DATABASE_URL')

    logger.info("=" * 70)
    logger.info("USDA Census/Survey Data ETL Flow Started")
    logger.info("=" * 70)

    # Step 1: Extract
    logger.info("\n[Step 1] Extracting USDA data...")
    raw_data = extract()

    if raw_data is None:
        logger.error("✗ Extract failed. Aborting flow.")
        return False

    logger.info(f"✓ Extract complete: {len(raw_data)} records retrieved")

    # Step 2: Transform
    logger.info("\n[Step 2] Transforming raw data...")
    data_sources = {"usda_census_survey": raw_data}
    cleaned_data = transform(data_sources)

    if cleaned_data is None:
        logger.error("✗ Transform failed. Aborting flow.")
        return False

    logger.info(f"✓ Transform complete: {len(cleaned_data)} records cleaned")

    # Step 3: Load
    logger.info("\n[Step 3] Loading data into database...")
    success = load(cleaned_data)

    if success:
        logger.info(f"✓ Load complete: {len(cleaned_data)} records loaded")
    else:
        logger.error("✗ Load failed.")
        return False

    # Step 4: Link records to datasets (data lineage)
    logger.info("\n[Step 4] Linking records to datasets for data lineage...")

    census_link_result = link_census_records_to_datasets(db_url=db_url)
    logger.info(
        f"✓ Linked {census_link_result['updated']} census records "
        f"(years: {census_link_result['years']})"
    )

    survey_link_result = link_survey_records_to_datasets(db_url=db_url)
    logger.info(
        f"✓ Linked {survey_link_result['updated']} survey records "
        f"(years: {survey_link_result['years']})"
    )

    obs_link_result = link_observations_to_datasets(db_url=db_url)
    logger.info(
        f"✓ Linked {obs_link_result['census_linked']} census observations + "
        f"{obs_link_result['survey_linked']} survey observations"
    )

    # Step 5: Verify linkage
    logger.info("\n[Step 5] Verifying data lineage linkage...")
    verify_result = verify_dataset_linkage(db_url=db_url)

    # Check for issues
    has_issues = False
    if verify_result['census_missing'] > 0:
        logger.warning(
            f"⚠ WARNING: {verify_result['census_missing']} census records missing dataset_id"
        )
        has_issues = True
    if verify_result['survey_missing'] > 0:
        logger.warning(
            f"⚠ WARNING: {verify_result['survey_missing']} survey records missing dataset_id"
        )
        has_issues = True
    if verify_result['obs_missing'] > 0:
        logger.warning(
            f"⚠ WARNING: {verify_result['obs_missing']} observations missing dataset_id"
        )
        has_issues = True

    if not has_issues:
        logger.info("✓ All records successfully linked to datasets")

    logger.info("\n" + "=" * 70)
    logger.info("✓ USDA ETL Flow Completed Successfully")
    logger.info("=" * 70)

    return {
        "extracted": len(raw_data),
        "loaded": len(cleaned_data),
        "census_linked": census_link_result['updated'],
        "survey_linked": survey_link_result['updated'],
        "observations_linked": obs_link_result['census_linked'] + obs_link_result['survey_linked'],
        "verification": verify_result,
    }


if __name__ == "__main__":
    # Can run directly: python usda_etl.py
    result = usda_etl_flow()
    if result:
        print("\n✓ Flow execution successful!")
    else:
        print("\n✗ Flow execution failed!")
