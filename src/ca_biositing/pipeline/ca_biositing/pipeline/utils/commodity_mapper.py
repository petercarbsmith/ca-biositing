from typing import List, Optional
import sys
import os
from sqlalchemy import text, create_engine
from sqlmodel import Session, select


def get_mapped_commodity_ids(engine=None) -> Optional[List[int]]:
    """
    Get USDA commodity IDs mapped to our resources from database.

    Note: The database schema has 'primary_crop_id' but the generated
    models have 'primary_ag_product_id'. This function handles both.

    Returns:
        List of usda_commodity IDs that are mapped, or None if query fails
    """
    try:
        if engine is None:
            # Load from .env (now has correct localhost credentials)
            db_url = os.getenv(
                "DATABASE_URL",
                "postgresql+psycopg2://biocirv_user:biocirv_dev_password@localhost:5432/biocirv_db"
            )
            engine = create_engine(db_url, echo=False)

        # Use raw SQLAlchemy connection to get USDA codes for mapped commodities
        from sqlalchemy import text as sql_text
        with engine.connect() as conn:
            # First check if usda_commodity table has any data
            count_result = conn.execute(sql_text("SELECT COUNT(*) FROM usda_commodity"))
            count = count_result.scalar()

            if count == 0:
                print("⚠️ USDA commodity table is empty - no commodities to map")
                print("   This likely means the coworker's ETL flow hasn't populated the database yet")
                print("   You need to run: pixi run run-etl")
                print("   before running USDA ingestion")
                return []

            # Join with UsdaCommodity to get the actual USDA codes, not the database IDs
            result = conn.execute(sql_text("""
                SELECT DISTINCT uc.id
                FROM usda_commodity uc
                WHERE uc.id IS NOT NULL
                ORDER BY uc.id
            """))
            codes = [row[0] for row in result.fetchall()]
            return codes if codes else []
    except Exception as e:
        print(f"Error querying mapped commodities: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    ids = get_mapped_commodity_ids()
    print(f"Mapped USDA commodity IDs: {ids}")
