# USDA Pipeline Redesign: Complete Summary

## What Was Done

Your three questions were answered with comprehensive guidance:

### 1. **Names vs IDs** ✅

- Created [USDA_NAMES_QUICK_REFERENCE.md](USDA_NAMES_QUICK_REFERENCE.md) with
  complete name-based workflow
- All code uses commodity names like "ALMONDS", "CORN" (not numeric IDs)
- Includes working examples of bootstrap, mapping, and extraction using names

### 2. **Architecture Decision** ✅

- Created [USDA_DATA_IMPORT_STRATEGY.md](USDA_DATA_IMPORT_STRATEGY.md) analyzing
  three options
- Recommended: Option C (Hybrid) - Database-driven filtering
- Business logic (which crops matter) → Database
- Operational logic (how to fetch data) → Code
- Result: Scalable system that grows without code changes

### 3. **Timeline Clarification** ✅

- Created [USDA_BOOTSTRAP_CLARIFICATIONS.md](USDA_BOOTSTRAP_CLARIFICATIONS.md)
  with three timeline options
- 1-day intensive (6-7 hours, all at once)
- 2-3 day hybrid (4-5 hours spread, **recommended for most teams**)
- 5-8 week conservative (part-time with reviews)
- Total actual work: 4-6 hours (just varies how you spread it)

---

## Documentation Created (8 Files)

All files are in `docs/` folder:

| File                                                                         | Purpose                                   | Read Time |
| ---------------------------------------------------------------------------- | ----------------------------------------- | --------- |
| [START_HERE.md](START_HERE.md)                                               | **Roadmap & navigation guide**            | 10 min    |
| [USDA_NAMES_QUICK_REFERENCE.md](USDA_NAMES_QUICK_REFERENCE.md)               | Complete name-based workflow with code    | 15 min    |
| [USDA_DATA_IMPORT_STRATEGY.md](USDA_DATA_IMPORT_STRATEGY.md)                 | Three options analysis & architecture     | 20 min    |
| [USDA_BOOTSTRAP_CLARIFICATIONS.md](USDA_BOOTSTRAP_CLARIFICATIONS.md)         | Timeline options (1-day, 2-3 day, 5-week) | 15 min    |
| [USDA_IMPLEMENTATION_CHECKLIST.md](USDA_IMPLEMENTATION_CHECKLIST.md)         | 8-phase step-by-step implementation       | Reference |
| [USDA_API_MIGRATION_GUIDE.md](USDA_API_MIGRATION_GUIDE.md)                   | Complete API documentation                | Reference |
| [USDA_EXTRACT_ENHANCEMENT_TACTICAL.md](USDA_EXTRACT_ENHANCEMENT_TACTICAL.md) | Technical deep-dive & optimization        | Reference |
| [USDA_DOCUMENTATION_INDEX.md](USDA_DOCUMENTATION_INDEX.md)                   | Complete document index                   | 5 min     |

**Also created**: [USDA_IMPORT_DECISION_TREE.md](USDA_IMPORT_DECISION_TREE.md)
and [USDA_STRATEGY_SUMMARY.md](USDA_STRATEGY_SUMMARY.md)

---

## The Architecture (Recommended Option C)

```
┌──────────────────────────────────────────────┐
│ BOOTSTRAP (One-time Setup)                   │
├──────────────────────────────────────────────┤
│                                              │
│ Your team lists commodities:                 │
│ ["ALMONDS", "CORN", "WHEAT"]                 │
│            ↓                                  │
│ Flow inserts into usda_commodity table       │
│            ↓                                  │
│ Team creates resource mappings:              │
│ Your Almond crop → USDA ALMONDS             │
│                                              │
└──────────────────────────────────────────────┘
              ↓
┌──────────────────────────────────────────────┐
│ OPERATIONAL (Every ETL Run)                  │
├──────────────────────────────────────────────┤
│                                              │
│ 1. Extract queries database:                 │
│    SELECT usda_commodity_names               │
│    Result: ["ALMONDS", "CORN"]              │
│            ↓                                  │
│ 2. Calls USDA API with names:               │
│    ?commodity_desc=ALMONDS&state=CA         │
│    ?commodity_desc=CORN&state=CA            │
│            ↓                                  │
│ 3. Loads data into usda_survey_record        │
│            ↓                                  │
│ 4. Matches against resource_usda_commodity   │
│    to get final filtered dataset             │
│                                              │
└──────────────────────────────────────────────┘
```

**Benefits**:

- ✅ Add new crops: Update database, not code
- ✅ User-friendly: See "CORN" not "5" in logs
- ✅ Scalable: Grows as your resource list grows
- ✅ Clean separation: Business logic (database) vs operational logic (code)

---

## Implementation Path (Choose Your Speed)

### Option A: 1-Day Intensive (6-7 hours)

**For**: Developers with blocked time, confident in their environment

```
Uninterrupted block of 6-7 hours:
- Create commodity_mapper.py (30 min)
- Create bootstrap flow (30 min)
- Run bootstrap + create mappings (30 min)
- Local testing (1.5 hours)
- Deploy to Docker (1 hour)
- Verify in database (30 min)
→ Production-ready same day
```

### Option B: 2-3 Days Hybrid ⭐ RECOMMENDED

**For**: Most teams; balances speed with sanity checks

```
Day 1 (4 hours):
- Create commodity_mapper.py (30 min)
- Create bootstrap flow (30 min)
- Local unit tests (1 hour)
- Code review (1 hour)

Day 2 (3 hours):
- Run bootstrap (30 min)
- Create database mappings (30 min)
- Integration testing (1 hour)
- Deploy to staging (30 min)

Day 3 (2 hours):
- Full pipeline test (1 hour)
- Data quality check (30 min)
- Move to production (30 min)
→ 9 hours total, spread across 3 days
```

### Option C: 5-8 Week Conservative

**For**: Teams with less DevOps experience or tighter schedules

Spreads the same 4-6 hours of work across weeks with multiple review cycles.

---

## What You Need to Do

### Phase 1: Understand (30 minutes)

1. Read [USDA_DATA_IMPORT_STRATEGY.md](USDA_DATA_IMPORT_STRATEGY.md)
2. Skim [USDA_NAMES_QUICK_REFERENCE.md](USDA_NAMES_QUICK_REFERENCE.md)
3. Choose timeline in
   [USDA_BOOTSTRAP_CLARIFICATIONS.md](USDA_BOOTSTRAP_CLARIFICATIONS.md)

### Phase 2: Code (4-6 hours of work)

Follow [USDA_IMPLEMENTATION_CHECKLIST.md](USDA_IMPLEMENTATION_CHECKLIST.md):

- Create `commodity_mapper.py` (query database for commodity names)
- Create `bootstrap_usda_commodities.py` (populate usda_commodity table)
- Create database mappings (link your crops to USDA commodities)
- Test locally
- Deploy to Docker

### Phase 3: Deploy & Verify (1-2 hours)

- Run integration tests
- Verify data quality
- Move to production

---

## Code: The Name-Based Approach

### 1. Bootstrap (Simple Manual List)

```python
# Your team just lists the commodities they care about
COMMODITIES_TO_ADD = [
    "ALMONDS",
    "CORN",
    "WHEAT",
    "SOYBEANS",
]

# Bootstrap flow adds them to database
for name in COMMODITIES_TO_ADD:
    commodity = UsdaCommodity(name=name, usda_source="NASS")
    session.add(commodity)
```

### 2. Query Database for Names

```python
# Get NAMES (not IDs) from database
def get_mapped_commodity_names() -> List[str]:
    with Session(engine) as session:
        statement = select(UsdaCommodity.name).where(
            UsdaCommodity.id.in_(
                select(ResourceUsdaCommodityMap.usda_commodity_id)
            )
        ).distinct()
        return list(session.exec(statement).all())

# Result: ["ALMONDS", "CORN"]
```

### 3. Extract Using Names

```python
@task
def extract() -> pd.DataFrame:
    # Read commodity NAMES from database
    commodity_names = get_mapped_commodity_names()

    # Call USDA API with names (not IDs)
    raw_df = usda_nass_to_df(
        api_key=USDA_API_KEY,
        commodity_names=commodity_names  # ← Names!
    )
    return raw_df
```

### 4. Database Mappings (SQL)

```sql
-- Link your crops to USDA commodities by NAME
INSERT INTO resource_usda_commodity_map
  (primary_ag_product_id, usda_commodity_id, match_tier)
SELECT
  1,  -- Your Almond crop
  uc.id,  -- USDA commodity (looked up by name)
  'DIRECT_MATCH'
FROM usda_commodity uc
WHERE uc.name = 'ALMONDS';  -- ← Use NAME!
```

---

## Timeline Summary

| Aspect          | 1-Day              | 2-3 Day         | 5-Week             |
| --------------- | ------------------ | --------------- | ------------------ |
| **Effort**      | 6-7 hours straight | 4 + 3 + 2 hours | 1 hr/week          |
| **Setup**       | Challenging        | Straightforward | Very comfortable   |
| **Reviews**     | Few                | Multiple        | Many               |
| **Speed**       | Very fast          | Balanced        | Conservative       |
| **Recommended** | ✅ If blocked      | ✅ Most teams   | ✅ Slow onboarding |

---

## Where to Go Next

### I want to understand the big picture

→ Start with [USDA_DATA_IMPORT_STRATEGY.md](USDA_DATA_IMPORT_STRATEGY.md)

### I want to see working code immediately

→ Jump to [USDA_NAMES_QUICK_REFERENCE.md](USDA_NAMES_QUICK_REFERENCE.md)

### I want to pick my timeline

→ Read [USDA_BOOTSTRAP_CLARIFICATIONS.md](USDA_BOOTSTRAP_CLARIFICATIONS.md)

### I'm ready to start implementing

→ Follow [USDA_IMPLEMENTATION_CHECKLIST.md](USDA_IMPLEMENTATION_CHECKLIST.md)

### I need technical deep-dives

→ See [USDA_API_MIGRATION_GUIDE.md](USDA_API_MIGRATION_GUIDE.md) or
[USDA_EXTRACT_ENHANCEMENT_TACTICAL.md](USDA_EXTRACT_ENHANCEMENT_TACTICAL.md)

### I need the navigation guide

→ Open [START_HERE.md](START_HERE.md)

---

## Key Decisions Made for You

1. **Names over IDs** ✅
   - User-friendly in logs and queries
   - Matches USDA API's native commodity_desc parameter
   - Makes code more maintainable

2. **Database-driven filtering** ✅
   - Business logic lives in database (resource_usda_commodity_map)
   - Operational logic lives in code (how to query)
   - Scales without code changes

3. **Manual bootstrap over API discovery** ✅
   - Simpler and more transparent
   - Team directly controls which commodities exist
   - No hidden API calls in setup phase

4. **2-3 day hybrid timeline recommended** ✅
   - Balances speed with sanity checks
   - Allows code review between phases
   - Spreads work comfortably across reasonable time

---

## Success Criteria

By end of implementation, you'll have:

- ✅ Commodity names stored in `usda_commodity` table
- ✅ Mappings created in `resource_usda_commodity_map` table
- ✅ `commodity_mapper.py` querying database for commodity names
- ✅ `usda_census_survey.py` extract function reading from database
- ✅ `usda_nass_to_pandas.py` utility accepting commodity names
- ✅ Bootstrap flow working one-time setup
- ✅ Integration tests passing
- ✅ Full ETL pipeline running from USDA API
- ✅ Data appearing in database with correct mappings

---

## Questions?

| Question                  | Answer                                                           | Document                                 |
| ------------------------- | ---------------------------------------------------------------- | ---------------------------------------- |
| Why names instead of IDs? | Better UX, matches USDA API                                      | USDA_NAMES_QUICK_REFERENCE.md            |
| Where does logic live?    | Business logic in DB, operational logic in code                  | USDA_DATA_IMPORT_STRATEGY.md             |
| How long will it take?    | 4-6 hours work, spread your choice (1 day, 2-3 days, or 5 weeks) | USDA_BOOTSTRAP_CLARIFICATIONS.md         |
| Show me working code      | Complete examples included                                       | USDA_NAMES_QUICK_REFERENCE.md            |
| How do I bootstrap?       | Manual list of commodity names                                   | USDA_BOOTSTRAP_CLARIFICATIONS.md         |
| How do I map crops?       | SQL templates provided                                           | USDA_IMPLEMENTATION_CHECKLIST.md Phase 6 |
| What about errors?        | Troubleshooting guide included                                   | USDA_IMPLEMENTATION_CHECKLIST.md Phase 7 |

---

**Last Updated**: After Message 5 of your conversation

**Status**: All questions answered, complete implementation path defined,
working code provided

**Ready to start?** Open [START_HERE.md](START_HERE.md) 👈
