from prefect import flow, task, get_run_logger
from ca_biositing.pipeline.utils.usda_nass_to_pandas import get_available_parameters
from ca_biositing.datamodels import UsdaCommodity
from sqlmodel import Session
from ca_biositing.datamodels.database import engine
import os

@task
def fetch_commodities_from_api(api_key: str):
    """Download list of all NASS commodities from USDA API."""
    logger = get_run_logger()
    logger.info("Fetching commodity list from USDA NASS API...")

    params = get_available_parameters(api_key)

    if "commodity_desc" not in params:
        logger.error("Failed to fetch commodities")
        return None

    logger.info(f"Found {len(params['commodity_desc'])} commodities")
    return params['commodity_desc']

@task
def insert_commodities(commodity_names):
    """Insert commodities into usda_commodity table."""
    logger = get_run_logger()
    logger.info(f"Inserting {len(commodity_names)} commodities into database...")

    with Session(engine) as session:
        for name in commodity_names:
            # Check if already exists
            existing = session.query(UsdaCommodity).filter(
                UsdaCommodity.name == name
            ).first()

            if not existing:
                commodity = UsdaCommodity(
                    name=name,
                    usda_source="NASS",
                    description=f"NASS commodity: {name}"
                )
                session.add(commodity)

        session.commit()

    logger.info("Bootstrap complete!")

@flow(name="Bootstrap USDA Commodities")
def bootstrap_usda_commodities():
    """One-time: Download all USDA commodities and populate lookup table."""
    api_key = os.getenv("USDA_NASS_API_KEY")

    if not api_key:
        print("ERROR: USDA_NASS_API_KEY not set in environment")
        return

    commodities = fetch_commodities_from_api(api_key)
    if commodities:
        insert_commodities(commodities)

# Don't forget to register this with Prefect!
# Add to your deployment configuration
