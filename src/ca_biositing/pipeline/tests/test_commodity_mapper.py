import pytest
from sqlmodel import Session
from ca_biositing.datamodels.database import Base
from ca_biositing.datamodels.schemas.generated.ca_biositing import ResourceUsdaCommodityMap
from ca_biositing.pipeline.utils.commodity_mapper import get_mapped_commodity_ids

def test_get_mapped_commodity_ids(session: Session):
    # Create tables in the in-memory database
    Base.metadata.create_all(session.get_bind())

    # Insert a mapping record
    mapping = ResourceUsdaCommodityMap(
        resource_id=1,
        primary_ag_product_id=1,
        usda_commodity_id=123,
        match_tier="1",
        note="test",
        etl_run_id=None,
        lineage_group_id=None
    )
    session.add(mapping)
    session.commit()

    # Use the session's engine to test the function
    engine = session.get_bind()
    result = get_mapped_commodity_ids(engine)

    assert isinstance(result, list)
    assert 123 in result
