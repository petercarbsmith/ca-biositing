# Bootstrap & Implementation: Practical Clarifications

## Question 1: Using Commodity Names Instead of IDs

**Short answer**: YES! Use names. It's more user-friendly and the database
handles IDs automatically.

### Why Names Are Better

The USDA API returns data using **commodity descriptions (names)**, not numeric
IDs:

```json
{
  "commodity_desc": "CORN", // ← This is what the API gives you
  "commodity_code": 12010, // ← This is internal USDA code
  "state_alpha": "CA",
  "year": 2023,
  "Value": 50000
}
```

Your database should map:

- **Names** (text) → What you see and work with
- **IDs** (auto-increment) → Internal database identifiers

---

## Enhanced Bootstrap Approach: Name-Based

### Option A: Your Team Manually Lists Commodities (Simplest)

Instead of fetching from API, your team just says:

```python
# resources/prefect/flows/bootstrap_usda_commodities.py

# Define commodities YOUR team cares about (simpler!)
INITIAL_COMMODITIES = [
    {"name": "ALMONDS", "usda_source": "NASS"},
    {"name": "CORN", "usda_source": "NASS"},
    {"name": "WHEAT", "usda_source": "NASS"},
    {"name": "SOYBEANS", "usda_source": "NASS"},
]

@task
def bootstrap_commodities_manual():
    """Insert commodities directly (no API call needed)."""
    from sqlmodel import Session
    from ca_biositing.datamodels import UsdaCommodity
    from ca_biositing.datamodels.database import engine

    with Session(engine) as session:
        for comm in INITIAL_COMMODITIES:
            # Check if exists (by name)
            existing = session.query(UsdaCommodity).filter(
                UsdaCommodity.name == comm["name"]
            ).first()

            if not existing:
                new_commodity = UsdaCommodity(
                    name=comm["name"],
                    usda_source=comm["usda_source"],
                    description=f"{comm['usda_source']} commodity: {comm['name']}"
                )
                session.add(new_commodity)

        session.commit()

    print("✓ Bootstrap complete!")
```

**Advantages**:

- ✅ No API calls needed
- ✅ Your team explicitly controls which commodities exist
- ✅ Simple and transparent
- ✅ Easy to add more later by editing the list

---

### Option B: Fetch from API but Work with Names

```python
# More sophisticated, but still name-based

@task
def bootstrap_commodities_from_api(api_key: str):
    """Fetch commodities from API by name."""
    from ca_biositing.pipeline.utils.usda_nass_to_pandas import get_available_parameters
    from sqlmodel import Session
    from ca_biositing.datamodels import UsdaCommodity
    from ca_biositing.datamodels.database import engine

    # Get commodity NAMES from API
    params = get_available_parameters(api_key)
    commodity_names = params.get("commodity_desc", [])

    print(f"Found {len(commodity_names)} commodities: {commodity_names[:5]}...")

    # Insert using NAMES (not IDs)
    with Session(engine) as session:
        for name in commodity_names:
            existing = session.query(UsdaCommodity).filter(
                UsdaCommodity.name == name
            ).first()

            if not existing:
                new_commodity = UsdaCommodity(
                    name=name,                              # ← NAME
                    usda_source="NASS",
                    description=f"NASS commodity: {name}"
                )
                session.add(new_commodity)

        session.commit()

    print(f"✓ Inserted {len(commodity_names)} commodities")
```

**Advantages**:

- ✅ Gets all available commodities from USDA
- ✅ Still uses names throughout
- ✅ Database auto-assigns IDs

---

## Revised Extract: Working with Names

Your extract can query by **name** instead of ID:

```python
# src/ca_biositing/pipeline/ca_biositing/pipeline/etl/extract/usda_census_survey.py

from pipeline.utils.commodity_mapper import get_mapped_commodity_names

@task
def extract() -> Optional[pd.DataFrame]:
    """
    Extract USDA data for mapped commodities (using NAMES, not IDs).
    """
    logger = get_run_logger()

    # Get commodity NAMES from database
    commodity_names = get_mapped_commodity_names()

    if not commodity_names:
        logger.warning("No commodity mappings found...")
        return None

    logger.info(f"Extracting data for: {', '.join(commodity_names)}")

    # Query API by name
    raw_df = usda_nass_to_df(
        api_key=USDA_API_KEY,
        state=STATE,
        year=YEAR,
        commodity_names=commodity_names  # ← Use NAMES!
    )

    if raw_df is None:
        logger.error("Failed to extract.")
        return None

    logger.info(f"Successfully extracted {len(raw_df)} records.")
    return raw_df
```

---

## Updated Utility: Accept Names

```python
# src/ca_biositing/pipeline/ca_biositing/pipeline/utils/usda_nass_to_pandas.py

def usda_nass_to_df(
    api_key: str,
    state: str = "CA",
    year: Optional[int] = None,
    commodity: Optional[str] = None,
    commodity_names: Optional[List[str]] = None,  # ← NEW: Accept names
    **kwargs
) -> Optional[pd.DataFrame]:
    """
    Fetch USDA data using commodity NAMES (not IDs).

    Args:
        commodity_names: List of names like ["CORN", "ALMONDS", "WHEAT"]
    """
    BASE_URL = "https://quickstats.nass.usda.gov/api/api_GET"
    params = {
        "key": api_key,
        "state_alpha": state,
        "format": "JSON",
    }

    if year is not None:
        params["year"] = year

    # Handle commodity NAMES
    if commodity_names is not None:
        all_dfs = []

        for name in commodity_names:
            logger.info(f"Querying {name}...")

            query_params = params.copy()
            query_params["commodity_desc"] = name  # ← API uses NAMES

            try:
                response = requests.get(BASE_URL, params=query_params, timeout=30)
                response.raise_for_status()
                data = response.json()

                if data and not isinstance(data, dict):
                    df = pd.DataFrame(data)
                    all_dfs.append(df)
                    logger.info(f"  {name}: {len(df)} records")
            except Exception as e:
                logger.error(f"  Error with {name}: {e}")

        if all_dfs:
            result = pd.concat(all_dfs, ignore_index=True)
            logger.info(f"Total: {len(result)} records")
            return result
        else:
            return pd.DataFrame()

    # Fallback to single commodity NAME
    if commodity is not None:
        params["commodity_desc"] = commodity

    params.update(kwargs)

    try:
        response = requests.get(BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, dict) and "error" in data:
            logger.error(f"USDA API Error: {data['error']}")
            return None

        if not data:
            return pd.DataFrame()

        return pd.DataFrame(data)
    except Exception as e:
        logger.error(f"Error: {e}")
        return None
```

---

## Updated Commodity Mapper Utility

```python
# src/ca_biositing/pipeline/ca_biositing/pipeline/utils/commodity_mapper.py

def get_mapped_commodity_names() -> Optional[List[str]]:
    """
    Get USDA commodity NAMES (text) that are mapped to our resources.

    Returns:
        List of names like ["CORN", "ALMONDS", "WHEAT"]
    """
    try:
        from sqlmodel import Session, select
        from ca_biositing.datamodels import ResourceUsdaCommodityMap, UsdaCommodity
        from ca_biositing.datamodels.database import engine

        with Session(engine) as session:
            # Join to get NAMES not IDs
            statement = select(UsdaCommodity.name).where(
                UsdaCommodity.id.in_(
                    select(ResourceUsdaCommodityMap.usda_commodity_id)
                )
            ).distinct()

            results = session.exec(statement).all()
            return list(results) if results else None
    except Exception as e:
        print(f"Error: {e}")
        return None


def get_mapped_commodity_ids() -> Optional[List[int]]:
    """
    Get USDA commodity IDs (for backward compatibility if needed).
    """
    try:
        from sqlmodel import Session, select
        from ca_biositing.datamodels import ResourceUsdaCommodityMap
        from ca_biositing.datamodels.database import engine

        with Session(engine) as session:
            statement = select(
                ResourceUsdaCommodityMap.usda_commodity_id
            ).distinct()

            results = session.exec(statement).all()
            return list(results) if results else None
    except Exception as e:
        print(f"Error: {e}")
        return None
```

---

## Manual Mapping: Now Using Names

```sql
-- Much easier to understand!

-- Step 1: Verify commodities exist by NAME
SELECT id, name FROM usda_commodity WHERE name IN ('ALMONDS', 'CORN');

-- Step 2: Create mappings using names (we reference the ID but understand by name)
INSERT INTO resource_usda_commodity_map
  (primary_ag_product_id, usda_commodity_id, match_tier, note)
SELECT
  1,                          -- primary_ag_product: Almond
  uc.id,                      -- usda_commodity.id (looked up by name)
  'DIRECT_MATCH',
  'Almond = ALMONDS (NASS)'
FROM usda_commodity uc
WHERE uc.name = 'ALMONDS';

-- Same for Corn
INSERT INTO resource_usda_commodity_map
  (primary_ag_product_id, usda_commodity_id, match_tier, note)
SELECT
  2,                          -- primary_ag_product: Corn
  uc.id,
  'DIRECT_MATCH',
  'Corn = CORN (NASS)'
FROM usda_commodity uc
WHERE uc.name = 'CORN';
```

---

## Summary: Names vs IDs

| Aspect          | Names (Text)            | IDs (Numbers)        |
| --------------- | ----------------------- | -------------------- |
| User-friendly   | ✅ YES                  | ❌ Hard to remember  |
| USDA API format | ✅ YES (API uses names) | ❌ Internal codes    |
| Debugging       | ✅ Easy to read logs    | ❌ Need lookup table |
| SQL queries     | ✅ Readable             | ❌ Need joins        |
| **Recommended** | ⭐ USE THIS             | ❌ Avoid             |

---

---

## Question 2: Why 5 Weeks Instead of 1 Day?

**Short answer**: The 5-week plan is **conservative/beginner-friendly**. You can
absolutely do it in **1 intensive day** (6-7 hours).

### The Two Paths

#### Path A: Conservative (5 Weeks)

```
Week 1: Preparation & understanding
  - Read docs (2 hours)
  - Review schema (1 hour)

Week 2: Create utilities (with testing between)
  - Create commodity_mapper.py
  - Test that it compiles & imports work

Week 3: Update extraction utilities
  - Modify usda_nass_to_pandas.py
  - Unit test

Week 4: Update extract function
  - Modify usda_census_survey.py
  - Integration test

Week 5: Bootstrap & deploy
  - Create bootstrap flow
  - Create database mappings
  - Run full pipeline
  - Monitor
```

**Why so spread out?**

- ✅ Time for your team to review each change
- ✅ Catch issues between phases
- ✅ Reduce risk of big integration problems
- ✅ Good for novice developers (breathing room)

---

#### Path B: Intensive (1 Day - 6-7 Hours)

```
Morning (3 hours):
  - Read USDA_DATA_IMPORT_STRATEGY.md (30 min)
  - Create commodity_mapper.py utility (1 hour)
  - Update usda_nass_to_pandas.py to accept names (1.5 hours)

Lunch (1 hour)

Afternoon (3 hours):
  - Update usda_census_survey.py extract (1 hour)
  - Create bootstrap flow (1 hour)
  - Setup database mappings & test (1 hour)

Deploy & Monitor (30 min - 1 hour)
```

**Why this works?**

- ✅ All code is straightforward (copy-paste from docs)
- ✅ No complex dependencies between phases
- ✅ Tests can run in parallel
- ✅ You'll catch issues immediately

---

## Which Path Should YOU Take?

| Factor                       | Conservative (5 weeks) | Intensive (1 day)    |
| ---------------------------- | ---------------------- | -------------------- |
| **Your time availability**   | Spread out             | Blocked full day     |
| **Your team's review speed** | Slow review cycle      | Can review quickly   |
| **Your confidence**          | New to this            | Confident in ETL     |
| **Risk tolerance**           | Low (slow rollout)     | Medium (fast deploy) |
| **Your coding pace**         | Deliberate             | Flow state           |
| **Recommended for you?**     | ✅ Maybe               | ⚠️ Possibly          |

---

## Recommended Timeline: Hybrid (2-3 Days)

**Best for most teams:**

```
Day 1 (4 hours):
  - Read docs + plan (1 hour)
  - Create all utilities + update functions (2 hours)
  - Local testing (1 hour)
  - ✓ Code review by teammate

Day 2 (3 hours):
  - Bootstrap commodities (30 min)
  - Create database mappings (30 min)
  - Integration testing (1 hour)
  - ✓ Team approval

Day 3 (1 hour):
  - Deploy to test environment
  - Monitor logs
  - ✓ Production ready
```

This gives you:

- ✅ Time to understand what you're building
- ✅ Time for team review between days
- ✅ Safe deployment window
- ✅ Enough breathing room to catch issues

---

## Updated Implementation Guide

Here's the **realistic timeline**:

### Option 1: If You Have Full Day Blocked (Do This!)

→ Follow the **1-day intensive path** → Code is simple enough to implement all
at once → Test locally before deploying

### Option 2: If Time Is Scattered

→ Use **2-3 day hybrid** (recommended) → Day 1: Code → Day 2: Integration → Day
3: Deploy

### Option 3: If You Want Maximum Safety

→ Use the **5-week conservative path** → Good for team familiarity → Good if
multiple people are learning

---

## Key Insight

The reason the tactical guide suggested 5 weeks was:

- Conservative estimate for novice developers
- Assumes you might not have blocked time
- Builds in team review cycles

**But the actual code is simple enough** that if you have a clear day, you can
do it all at once. The phases aren't blocked by complexity—they're just
checkpoints for validation.

---

## What I Recommend For You

Given that you:

1. ✅ Ask smart architectural questions
2. ✅ Understand your schema deeply
3. ✅ Want to use names (not IDs) - smart UX choice
4. ✅ Are asking practical timeline questions

**Recommendation**: Go with the **2-3 day hybrid approach**:

- Day 1: Code everything (follow the checklist)
- Day 2: Database mappings + integration test
- Day 3: Deploy + monitor

This gives you the speed of 1-day implementation with the safety of proper
testing between phases.

---

## Updated Checklist for 1-3 Day Implementation

### Day 1: Coding (3-4 hours)

- [ ] Create `commodity_mapper.py` (30 min)
- [ ] Update `usda_nass_to_pandas.py` to accept names (1 hour)
- [ ] Update `usda_census_survey.py` extract (1 hour)
- [ ] Create `bootstrap_usda_commodities.py` (1 hour)
- [ ] Local testing of all utilities (30 min)

### Day 2: Integration (2-3 hours)

- [ ] Run bootstrap flow to populate commodities (30 min)
- [ ] Create database mappings in SQL (30 min)
- [ ] Full integration test (1 hour)
- [ ] Resolve any issues (30 min)

### Day 3: Deployment (1-2 hours)

- [ ] Code review
- [ ] Deploy to test environment
- [ ] Run full pipeline
- [ ] Monitor logs
- [ ] Deploy to production (if all good)

**Total**: 6-7 hours across 3 days (you could compress to 1 day if needed)
