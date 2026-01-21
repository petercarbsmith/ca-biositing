from typing import List, Optional
from sqlmodel import Session, select
from ca_biositing.datamodels.schemas.generated.ca_biositing import ResourceUsdaCommodityMap

def get_mapped_commodity_ids(engine=None) -> Optional[List[int]]:
    """Get USDA commodity IDs mapped to our resources from database."""
    try:
        from ca_biositing.datamodels.database import engine as default_engine
        engine_to_use = engine or default_engine

        with Session(engine_to_use) as session:
            statement = select(
                ResourceUsdaCommodityMap.usda_commodity_id
            ).distinct()

            results = session.exec(statement).all()
            return list(results) if results else None
    except Exception as e:
        print(f"Error querying mapped commodities: {e}")
        return None

if __name__ == "__main__":
    ids = get_mapped_commodity_ids()
    print(f"Mapped USDA commodity IDs: {ids}")
