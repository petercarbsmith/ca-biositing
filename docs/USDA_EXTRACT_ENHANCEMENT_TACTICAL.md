# Tactical: Enhancing Your Extract Function for Option C

## Current State vs. Recommended State

### Current usda_census_survey.py

```python
@task
def extract() -> Optional[pd.DataFrame]:
    """Extracts all USDA data for California."""
    logger = get_run_logger()

    raw_df = usda_nass_to_df(
        api_key=USDA_API_KEY,
        state=STATE,
        year=YEAR,
        commodity=COMMODITY  # ← Hardcoded or None
    )

    if raw_df is None:
        logger.error("Failed to extract data from USDA API. Aborting.")
        return None

    logger.info(f"Successfully extracted {len(raw_df)} records from USDA NASS API.")
    return raw_df
```

**Issue**: The `commodity` parameter is either hardcoded or None (imports
everything).

---

### Recommended: Database-Driven Approach

```python
@task
def extract() -> Optional[pd.DataFrame]:
    """
    Extracts USDA data ONLY for commodities mapped to our resources.

    The list of commodities is read from resource_usda_commodity_map,
    not hardcoded. This makes adding new crops as easy as updating the database.
    """
    logger = get_run_logger()

    # CHANGE 1: Get commodity list from database
    mapped_commodity_ids = _get_mapped_commodity_ids()

    if not mapped_commodity_ids:
        logger.warning(
            "No commodity mappings found in resource_usda_commodity_map. "
            "Please populate this table and run bootstrap_usda_commodities flow first."
        )
        return None

    logger.info(
        f"Extracting USDA data for {len(mapped_commodity_ids)} mapped commodities..."
    )

    # CHANGE 2: Pass commodity IDs to extract function
    raw_df = usda_nass_to_df(
        api_key=USDA_API_KEY,
        state=STATE,
        year=YEAR,
        commodity_ids=mapped_commodity_ids  # ← From database, not config
    )

    if raw_df is None:
        logger.error("Failed to extract data from USDA API. Aborting.")
        return None

    logger.info(f"Successfully extracted {len(raw_df)} records from USDA NASS API.")
    return raw_df


def _get_mapped_commodity_ids() -> Optional[List[int]]:
    """
    Query database for USDA commodity IDs mapped to our resources.

    Returns:
        List of usda_commodity IDs, or None if query fails.
    """
    try:
        from sqlmodel import Session, select
        from ca_biositing.datamodels import ResourceUsdaCommodityMap

        # Import engine from database module
        from ca_biositing.datamodels.database import engine

        with Session(engine) as session:
            # Get all unique USDA commodity IDs that are mapped
            statement = select(
                ResourceUsdaCommodityMap.usda_commodity_id
            ).distinct()

            results = session.exec(statement).all()
            return results if results else None

    except Exception as e:
        print(f"Error querying mapped commodities: {e}")
        return None
```

---

## Changes to usda_nass_to_pandas.py Utility

### Current Function Signature

```python
def usda_nass_to_df(
    api_key: str,
    state: str = "CA",
    year: Optional[int] = None,
    commodity: Optional[str] = None,
    **kwargs
) -> Optional[pd.DataFrame]:
    """Fetches data from USDA API."""
    # ...
```

### Enhanced Function Signature

```python
def usda_nass_to_df(
    api_key: str,
    state: str = "CA",
    year: Optional[int] = None,
    commodity: Optional[str] = None,
    commodity_ids: Optional[List[int]] = None,  # ← NEW: Filter by ID
    **kwargs
) -> Optional[pd.DataFrame]:
    """
    Fetches agricultural data from the USDA NASS Quick Stats API.

    Args:
        api_key: Your USDA NASS API key
        state: State code (default: "CA")
        year: Optional year filter
        commodity: Optional commodity name (e.g., "CORN")
        commodity_ids: Optional list of commodity IDs to query
                      (Usually from resource_usda_commodity_map)
        **kwargs: Additional USDA API parameters

    Returns:
        DataFrame with USDA data, or None on error

    Note:
        If commodity_ids is provided, it takes precedence over commodity parameter.
        This allows database-driven queries without needing commodity names.
    """

    BASE_URL = "https://quickstats.nass.usda.gov/api/api_GET"
    params = {
        "key": api_key,
        "state_alpha": state,
        "format": "JSON",
    }

    if year is not None:
        params["year"] = year

    # HANDLE NEW PARAMETER: commodity_ids
    if commodity_ids is not None:
        # Query one commodity at a time (API constraint)
        # Aggregate results
        all_dfs = []

        for comm_id in commodity_ids:
            logger.info(f"Querying commodity ID {comm_id}...")

            # Add commodity ID to params
            params["commodity_code"] = comm_id  # ← USDA API accepts IDs

            response = requests.get(BASE_URL, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            if data and not isinstance(data, dict):
                df = pd.DataFrame(data)
                all_dfs.append(df)

        if all_dfs:
            return pd.concat(all_dfs, ignore_index=True)
        else:
            return pd.DataFrame()

    # FALLBACK: Use commodity name (old behavior)
    if commodity is not None:
        params["commodity_desc"] = commodity

    params.update(kwargs)

    try:
        response = requests.get(BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, dict) and "error" in data:
            print(f"USDA API Error: {data['error']}")
            return None

        if not data or len(data) == 0:
            print("No records found for the specified query.")
            return pd.DataFrame()

        df = pd.DataFrame(data)
        logger.info(f"Successfully retrieved {len(df)} records from USDA NASS API")
        return df

    except Exception as e:
        print(f"Error querying USDA NASS API: {e}")
        return None
```

---

## Step-by-Step Migration Plan

### Week 1: Understand Current State

```python
# Test current extract (should work as-is)
pixi run deploy
pixi run run-etl

# Observe: What gets imported? All commodities or just what's in COMMODITY config?
```

### Week 2: Create Database Utility

Add new function to pipeline utils:

```python
# src/ca_biositing/pipeline/ca_biositing/pipeline/utils/commodity_mapper.py

from typing import List, Optional
from sqlmodel import Session, select
from ca_biositing.datamodels import ResourceUsdaCommodityMap
from ca_biositing.datamodels.database import engine

def get_mapped_commodity_ids() -> Optional[List[int]]:
    """
    Get list of USDA commodity IDs mapped to our resources.

    Query pattern:
        SELECT DISTINCT usda_commodity_id
        FROM resource_usda_commodity_map
        WHERE usda_commodity_id IS NOT NULL
    """
    try:
        with Session(engine) as session:
            statement = select(
                ResourceUsdaCommodityMap.usda_commodity_id
            ).distinct()
            results = session.exec(statement).all()
            return list(results) if results else None
    except Exception as e:
        print(f"Error querying mapped commodities: {e}")
        return None

def get_mapped_commodity_names() -> Optional[List[str]]:
    """
    Get names of commodities (for reference/debugging).
    """
    try:
        with Session(engine) as session:
            # Join with usda_commodity to get names
            from ca_biositing.datamodels import UsdaCommodity

            statement = select(UsdaCommodity.name).where(
                UsdaCommodity.id.in_(
                    select(ResourceUsdaCommodityMap.usda_commodity_id)
                )
            ).distinct()

            results = session.exec(statement).all()
            return list(results) if results else None
    except Exception as e:
        print(f"Error querying commodity names: {e}")
        return None
```

### Week 3: Update Extract Function

```python
# src/ca_biositing/pipeline/ca_biositing/pipeline/etl/extract/usda_census_survey.py

# Add import
from pipeline.utils.commodity_mapper import get_mapped_commodity_ids

# Add new task
@task
def extract() -> Optional[pd.DataFrame]:
    """Extracts USDA data for mapped commodities."""
    logger = get_run_logger()

    # Get mapped commodities from database
    commodity_ids = get_mapped_commodity_ids()

    if not commodity_ids:
        logger.warning(
            "No commodity mappings found. "
            "Run bootstrap_usda_commodities flow to populate resource_usda_commodity_map."
        )
        return None

    logger.info(f"Extracting data for {len(commodity_ids)} commodities...")

    # Use new parameter in utility
    raw_df = usda_nass_to_df(
        api_key=USDA_API_KEY,
        state=STATE,
        year=YEAR,
        commodity_ids=commodity_ids  # ← NEW: Database-driven
    )

    if raw_df is None:
        logger.error("Failed to extract data from USDA API. Aborting.")
        return None

    logger.info(f"Successfully extracted {len(raw_df)} records.")
    return raw_df
```

### Week 4: Update Utility Function

```python
# Update usda_nass_to_pandas.py with commodity_ids parameter
# (See "Enhanced Function Signature" section above)
```

### Week 5: Create Bootstrap Flow

```python
# resources/prefect/flows/bootstrap_usda_commodities.py

from prefect import flow, task
from ca_biositing.pipeline.utils.usda_nass_to_pandas import get_available_parameters
from ca_biositing.datamodels import UsdaCommodity
from sqlmodel import Session
from ca_biositing.datamodels.database import engine

@task
def fetch_commodities_from_api(api_key: str):
    """Fetch list of all available NASS commodities."""
    logger = get_run_logger()
    logger.info("Fetching NASS commodity list from API...")

    params = get_available_parameters(api_key)

    if "commodity_desc" not in params:
        logger.error("Failed to fetch commodities from API.")
        return None

    return params["commodity_desc"]

@task
def populate_commodity_table(commodities: List[str]):
    """Insert commodities into usda_commodity table."""
    logger = get_run_logger()
    logger.info(f"Inserting {len(commodities)} commodities into usda_commodity...")

    with Session(engine) as session:
        for commodity_name in commodities:
            # Check if already exists
            existing = session.query(UsdaCommodity).filter(
                UsdaCommodity.name == commodity_name
            ).first()

            if not existing:
                new_commodity = UsdaCommodity(
                    name=commodity_name,
                    usda_source="NASS",
                    description=f"NASS commodity: {commodity_name}",
                )
                session.add(new_commodity)

        session.commit()

    logger.info("Bootstrap complete!")

@flow(name="Bootstrap USDA Commodities")
def bootstrap_usda_commodities_flow():
    """One-time setup: populate usda_commodity lookup table."""
    api_key = os.getenv("USDA_NASS_API_KEY")

    if not api_key:
        print("ERROR: USDA_NASS_API_KEY not set in environment")
        return

    commodities = fetch_commodities_from_api(api_key)
    if commodities:
        populate_commodity_table(commodities)
```

---

## Testing Your Changes

### Test 1: Verify Database Utility Works

```python
# In a notebook or script:
from pipeline.utils.commodity_mapper import get_mapped_commodity_ids

commodity_ids = get_mapped_commodity_ids()
print(f"Found {len(commodity_ids) if commodity_ids else 0} mapped commodities")

# Should return: None (if no mappings yet) or [1, 5, 12, ...] (if mappings exist)
```

### Test 2: Test Extract with Mappings

```python
# After creating mappings in resource_usda_commodity_map:

from pipeline.etl.extract.usda_census_survey import extract

df = extract()
print(df.head())
print(f"Extracted {len(df)} records")

# Should return records ONLY for mapped commodities
```

### Test 3: Run Full Pipeline

```bash
pixi run deploy
pixi run run-etl
```

---

## Benefits of This Approach

| Benefit               | How It Works                                              |
| --------------------- | --------------------------------------------------------- |
| **No Hardcoding**     | Commodities defined in database, not config               |
| **Easy to Add Crops** | Just add row to resource_usda_commodity_map               |
| **Discovery**         | Can see all available commodities in usda_commodity table |
| **Audit Trail**       | Database query history shows what was imported            |
| **Scalable**          | Adding 10 new crops = 10 SQL inserts (no code!)           |
| **Testable**          | Utility function can be tested independently              |

---

## Common Questions

**Q: What if I want to temporarily import ALL commodities for testing?**

A: Just set `commodity_ids=None` in the extract call:

```python
raw_df = usda_nass_to_df(
    api_key=USDA_API_KEY,
    state=STATE,
    year=2023,
    # commodity_ids=None  ← Falls back to old behavior (imports all)
)
```

**Q: What if the API doesn't support commodity IDs?**

A: Update the utility to convert IDs to names first:

```python
def _get_commodity_names_from_ids(commodity_ids: List[int]) -> List[str]:
    """Convert database IDs to USDA commodity names."""
    with Session(engine) as session:
        names = session.query(UsdaCommodity.name).filter(
            UsdaCommodity.id.in_(commodity_ids)
        ).all()
        return [n[0] for n in names]
```

**Q: How do I add a new crop to the mappings?**

A: Just SQL:

```sql
-- Find the USDA commodity ID for wheat
SELECT id FROM usda_commodity WHERE name LIKE '%WHEAT%';
-- Result: id = 42

-- Create mapping
INSERT INTO resource_usda_commodity_map
  (primary_ag_product_id, usda_commodity_id, match_tier)
VALUES (6, 42, 'DIRECT_MATCH');

-- Next extract run automatically includes wheat!
```

---

## Summary

This tactical plan transforms your extract from **config-driven** to
**database-driven**:

- **Before**: Hardcoded commodities or imports everything
- **After**: Reads from database, scales with your business

You can implement this incrementally—start with the utility, add the database
query, then test before deploying. All without breaking your existing pipeline!
