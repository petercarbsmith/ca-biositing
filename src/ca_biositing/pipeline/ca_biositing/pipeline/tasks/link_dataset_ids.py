"""
Link records to datasets by year and source type.

This module provides idempotent Prefect tasks for linking USDA records
(usda_census_record, usda_survey_record, observation) to their corresponding
dataset entries.

The linking strategy is reproducible and database-driven:
1. Query existing datasets from database (no hardcoding)
2. Extract year and source_type from dataset name
3. Link records using (year, source_type) matching
4. All operations are idempotent (safe to re-run)
"""

from datetime import datetime, timezone
from prefect import task, get_run_logger
from sqlalchemy import create_engine, text
import os


@task(name="link-census-records-to-datasets")
def link_census_records_to_datasets(db_url: str = None) -> dict:
    """
    Link usda_census_record rows to their corresponding datasets.

    Uses year-based matching: census records are linked to datasets
    named USDA_CENSUS_YYYY where YYYY matches the record year.

    This task is idempotent - it only updates records with NULL dataset_id.

    Args:
        db_url: Database URL (defaults to DATABASE_URL env var)

    Returns:
        dict with update count and linked years
    """
    logger = get_run_logger()
    engine = create_engine(db_url or os.getenv('DATABASE_URL'))

    # Build mapping from (year, 'CENSUS') -> dataset_id
    dataset_map = {}
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, name FROM dataset
            WHERE name LIKE 'USDA_CENSUS_%'
            ORDER BY id
        """))
        for row in result:
            dataset_id, name = row
            try:
                year = int(name.split('_')[-1])
                dataset_map[year] = dataset_id
                logger.info(f"Mapped {name} (ID {dataset_id}) to year {year}")
            except (ValueError, IndexError):
                logger.warning(f"Could not parse year from dataset name: {name}")

    if not dataset_map:
        logger.warning("No USDA_CENSUS_* datasets found")
        return {"updated": 0, "years": []}

    # Link census records
    total_updated = 0
    with engine.begin() as conn:
        for year, dataset_id in dataset_map.items():
            result = conn.execute(text(f"""
                UPDATE usda_census_record
                SET dataset_id = {dataset_id}
                WHERE year = {year} AND dataset_id IS NULL
            """))
            updated = result.rowcount
            total_updated += updated
            logger.info(f"Linked {updated} census records for year {year} to dataset_id={dataset_id}")

    logger.info(f"Total census records linked: {total_updated}")
    return {"updated": total_updated, "years": list(dataset_map.keys())}


@task(name="link-survey-records-to-datasets")
def link_survey_records_to_datasets(db_url: str = None) -> dict:
    """
    Link usda_survey_record rows to their corresponding datasets.

    Uses year-based matching: survey records are linked to datasets
    named USDA_SURVEY_YYYY where YYYY matches the record year.

    This task is idempotent - it only updates records with NULL dataset_id.

    Args:
        db_url: Database URL (defaults to DATABASE_URL env var)

    Returns:
        dict with update count and linked years
    """
    logger = get_run_logger()
    engine = create_engine(db_url or os.getenv('DATABASE_URL'))

    # Build mapping from (year, 'SURVEY') -> dataset_id
    dataset_map = {}
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, name FROM dataset
            WHERE name LIKE 'USDA_SURVEY_%'
            ORDER BY id
        """))
        for row in result:
            dataset_id, name = row
            try:
                year = int(name.split('_')[-1])
                dataset_map[year] = dataset_id
                logger.info(f"Mapped {name} (ID {dataset_id}) to year {year}")
            except (ValueError, IndexError):
                logger.warning(f"Could not parse year from dataset name: {name}")

    if not dataset_map:
        logger.warning("No USDA_SURVEY_* datasets found")
        return {"updated": 0, "years": []}

    # Link survey records
    total_updated = 0
    with engine.begin() as conn:
        for year, dataset_id in dataset_map.items():
            result = conn.execute(text(f"""
                UPDATE usda_survey_record
                SET dataset_id = {dataset_id}
                WHERE year = {year} AND dataset_id IS NULL
            """))
            updated = result.rowcount
            total_updated += updated
            logger.info(f"Linked {updated} survey records for year {year} to dataset_id={dataset_id}")

    logger.info(f"Total survey records linked: {total_updated}")
    return {"updated": total_updated, "years": list(dataset_map.keys())}


@task(name="link-observations-to-datasets")
def link_observations_to_datasets(db_url: str = None) -> dict:
    """
    Link observation rows to their corresponding datasets.

    Uses record_type and year-based matching:
    - Observations with record_type='usda_census_record' link to USDA_CENSUS_YYYY datasets
    - Observations with record_type='usda_survey_record' link to USDA_SURVEY_YYYY datasets

    This task is idempotent - it only updates observations with NULL dataset_id.

    Args:
        db_url: Database URL (defaults to DATABASE_URL env var)

    Returns:
        dict with update counts by record type
    """
    logger = get_run_logger()
    engine = create_engine(db_url or os.getenv('DATABASE_URL'))

    results = {"census_linked": 0, "survey_linked": 0}

    # Link census observations
    with engine.begin() as conn:
        result = conn.execute(text("""
            UPDATE observation
            SET dataset_id = d.id
            FROM dataset d
            WHERE observation.dataset_id IS NULL
            AND observation.record_type = 'usda_census_record'
            AND d.name LIKE 'USDA_CENSUS_%'
            AND CAST(EXTRACT(YEAR FROM d.start_date) AS INTEGER) =
                (SELECT DISTINCT EXTRACT(YEAR FROM TO_TIMESTAMP(observation.record_id, 'YYYY-MM-DD'))
                 FROM observation obs2
                 WHERE obs2.id = observation.id)
        """))
        results["census_linked"] = result.rowcount
        logger.info(f"Linked {result.rowcount} census observations to datasets")

    # Link survey observations
    with engine.begin() as conn:
        result = conn.execute(text("""
            UPDATE observation
            SET dataset_id = d.id
            FROM dataset d
            WHERE observation.dataset_id IS NULL
            AND observation.record_type = 'usda_survey_record'
            AND d.name LIKE 'USDA_SURVEY_%'
        """))
        results["survey_linked"] = result.rowcount
        logger.info(f"Linked {result.rowcount} survey observations to datasets")

    total = results["census_linked"] + results["survey_linked"]
    logger.info(f"Total observations linked: {total}")
    return results


@task(name="verify-dataset-linkage")
def verify_dataset_linkage(db_url: str = None) -> dict:
    """
    Verify that all records are properly linked to datasets.

    Returns counts of records with and without dataset_id for each table.

    Args:
        db_url: Database URL (defaults to DATABASE_URL env var)

    Returns:
        dict with verification results
    """
    logger = get_run_logger()
    engine = create_engine(db_url or os.getenv('DATABASE_URL'))

    results = {}

    with engine.connect() as conn:
        # Check census records
        total = conn.execute(text("SELECT COUNT(*) FROM usda_census_record")).scalar()
        linked = conn.execute(text("SELECT COUNT(*) FROM usda_census_record WHERE dataset_id IS NOT NULL")).scalar()
        results["census_total"] = total
        results["census_linked"] = linked
        results["census_missing"] = total - linked
        logger.info(f"Census: {linked}/{total} linked")

        # Check survey records
        total = conn.execute(text("SELECT COUNT(*) FROM usda_survey_record")).scalar()
        linked = conn.execute(text("SELECT COUNT(*) FROM usda_survey_record WHERE dataset_id IS NOT NULL")).scalar()
        results["survey_total"] = total
        results["survey_linked"] = linked
        results["survey_missing"] = total - linked
        logger.info(f"Survey: {linked}/{total} linked")

        # Check observations
        total = conn.execute(text("SELECT COUNT(*) FROM observation")).scalar()
        linked = conn.execute(text("SELECT COUNT(*) FROM observation WHERE dataset_id IS NOT NULL")).scalar()
        results["obs_total"] = total
        results["obs_linked"] = linked
        results["obs_missing"] = total - linked
        logger.info(f"Observations: {linked}/{total} linked")

    # Check for issues
    if results["census_missing"] + results["survey_missing"] + results["obs_missing"] > 0:
        logger.warning("Some records still missing dataset_id linkage")
    else:
        logger.info("All records successfully linked to datasets!")

    return results
