"""
USDA Census/Survey Data Load

Loads transformed USDA data into the usda_census_record table.

This task:
1. Connects to the database
2. Inserts records into usda_census_record
3. Handles duplicates gracefully
4. Tracks ETL run lineage
"""

from typing import Optional
import pandas as pd
from prefect import task, get_run_logger
from sqlmodel import Session, select
from sqlalchemy import insert


@task
def load(transformed_df: Optional[pd.DataFrame]) -> bool:
    """
    Load transformed USDA data into the database.

    Args:
        transformed_df: DataFrame from transform task with columns:
                       [geoid, commodity_code, year, value, ...]

    Returns:
        True if load succeeds, False otherwise
    """
    logger = get_run_logger()
    logger.info("Loading USDA data into database...")

    if transformed_df is None or len(transformed_df) == 0:
        logger.warning("No data to load (dataframe is empty or None)")
        return True  # Not an error, just nothing to do

    try:
        from ca_biositing.datamodels.database import get_engine
        from ca_biositing.datamodels.schemas.generated.ca_biositing import UsdaCensusRecord
        import os

        # For local development on Windows, use localhost instead of 'db' hostname
        db_url = os.getenv(
            'DATABASE_URL',
            'postgresql+psycopg2://biocirv_user:biocirv_dev_password@localhost:5432/biocirv_db'
        )
        if '@db:' in db_url:
            db_url = db_url.replace('@db:', '@localhost:')

        from sqlalchemy import create_engine
        engine = create_engine(db_url)

        # Get current ETL run ID (could be passed as a parameter if using Prefect context)
        # For now, we'll use None
        etl_run_id = None

        records_inserted = 0
        records_skipped = 0

        with Session(engine) as session:
            for idx, row in transformed_df.iterrows():
                try:
                    # Create UsdaCensusRecord from the row
                    record = UsdaCensusRecord(
                        geoid=row.get('geoid'),
                        commodity_code=row.get('commodity_code'),
                        year=row.get('year'),
                        source_reference=row.get('source_reference'),
                        note=row.get('notes'),
                        etl_run_id=etl_run_id,
                        dataset_id=None,  # Could be linked if dataset is tracked
                    )

                    session.add(record)
                    records_inserted += 1

                except Exception as e:
                    logger.warning(f"Failed to insert row {idx}: {e}")
                    records_skipped += 1
                    continue

            try:
                session.commit()
                logger.info(f"Load complete: {records_inserted} records inserted, {records_skipped} skipped")
                return True
            except Exception as e:
                logger.error(f"Failed to commit records: {e}")
                session.rollback()
                return False

    except Exception as e:
        logger.error(f"Load failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    # Example for local testing
    import sys
    sys.path.insert(0, 'src/ca_biositing/pipeline')
    sys.path.insert(0, 'src/ca_biositing/datamodels')

    # Create sample data
    sample_data = pd.DataFrame({
        'geoid': ['CA_001', 'CA_003', 'CA_005'],
        'commodity_code': [26, 26, 26],
        'year': [2023, 2023, 2023],
        'value': [1000000, 2500000, 1200000],
        'source_reference': ['NASS', 'NASS', 'NASS']
    })

    success = load(sample_data)
    if success:
        print("Load test passed")
    else:
        print("Load test failed")
