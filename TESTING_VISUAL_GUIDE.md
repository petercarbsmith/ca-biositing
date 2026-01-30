# USDA ETL Testing Visual Guide

## Decision Tree: What Should I Do?

```
                          START
                            │
                            ▼
                    Is this my FIRST test?
                      /           \
                    YES            NO
                    │              │
        ┌───────────▼──────┐   ┌────▼─────────────┐
        │ Reset USDA data  │   │ Did it fail?    │
        │ (clean slate)    │   │                 │
        └────────┬─────────┘   │    /        \   │
                 │             │   YES       NO  │
                 │             │   │         │   │
                 │             │   │         │   │
                 │        ┌────▼───┴─────────┴──┐
                 │        │ Just run again     │
                 │        │ (dedup prevents   │
                 │        │  duplicates)      │
                 │        └──────────┬─────────┘
                 │                   │
                 ▼                   ▼
        ┌────────────────────────────────────┐
        │  Run: pixi run python -m           │
        │  src.ca_biositing.pipeline.flows   │
        │  .usda_etl                         │
        └────────┬─────────────────────────┬─┘
                 │                         │
            SUCCESS                    FAILURE
                 │                         │
                 ▼                         ▼
        ┌──────────────────┐    ┌──────────────────┐
        │ Run validation   │    │ Check logs:      │
        │ script           │    │ pixi run service │
        │ All ✓ = DONE!    │    │ -logs            │
        └──────────────────┘    └──────────────────┘
```

---

## State Machine: Service Lifecycle

```
┌─────────┐      pixi run          ┌─────────┐
│ STOPPED ├─────start-services────→│ RUNNING │
└─────────┘                        └────┬────┘
    ▲                                    │
    │      docker compose down           │
    └────────────────────────────────────┘

    (RUNNING state is where you do all testing)
    (Keep services here between test runs)
    (Just reset USDA data via SQL)
```

---

## Data Reset Strategy

```
ALL DATABASE DATA
    │
    ├─ Keep: Other data (LandIQ, Analysis, etc.)
    │
    └─ Delete: USDA Records
        │
        ├─ usda_census_record ← DELETE all rows
        ├─ usda_survey_record ← DELETE all rows
        ├─ observation (USDA only) ← DELETE matching rows
        └─ dataset (USDA only) ← DELETE matching rows

    Use script: scripts/reset_usda_data.sql
```

---

## Full ETL Flow: What Happens

```
EXTRACT (from USDA API)
    │
    ├─ Query USDA NASS QuickStats API
    ├─ Get Census + Survey data
    └─ Return raw_data DataFrame
         │
         ▼
TRANSFORM (normalize & map)
    │
    ├─ Create Parameters/Units (idempotent)
    ├─ Build lookup maps (commodity → ID, etc.)
    ├─ Construct geoid (FIPS code)
    ├─ Rename columns to schema names
    ├─ Clean strings (lowercase, null handling)
    ├─ Convert values to numeric
    ├─ Add record_type (census vs survey)
    ├─ Add metadata (etl_run_id, lineage_group_id)
    ├─ Generate note field
    └─ Filter required fields (drop nulls)
         │
         ▼
LOAD (insert into database)
    │
    ├─ STEP 0: Create/map datasets
    │   └─ USDA_CENSUS_2022, USDA_SURVEY_2022, etc.
    │
    ├─ STEP 1: Load Census Records
    │   ├─ Level 1 dedup: Skip if exists in DB
    │   ├─ Level 2 dedup: Skip if seen in batch
    │   └─ Insert with dataset linkage
    │
    ├─ STEP 2: Load Survey Records
    │   ├─ Capture survey_period, reference_month
    │   └─ Same dedup levels
    │
    └─ STEP 3: Load Observations
        ├─ Level 1 dedup: Skip if exists
        ├─ Level 2 dedup: Skip if seen
        ├─ Level 3 dedup: PostgreSQL ON CONFLICT
        └─ Insert with all metadata
         │
         ▼
VERIFY (success validation)
    │
    ├─ Census records > 0 ✓
    ├─ Survey records > 0 ✓
    ├─ Observations > 0 ✓
    ├─ 100% linked to datasets ✓
    ├─ 0 orphaned records ✓
    └─ etl_run_id tracked ✓
```

---

## Test Pyramid: What to Test

```
                    ▲
                   ╱ ╲      E2E Test
                  ╱   ╲    (Full flow)
                 ╱  ★  ╲   ← THIS: Most important for you
                ╱───────╲
               ╱         ╲  Integration
              ╱     ★★    ╲ (transform + load with real DB)
             ╱─────────────╲ ← OPTIONAL: If needed
            ╱               ╲
           ╱        ★★★      ╲ Unit Tests
          ╱───────────────────╲ (functions, mock data)
         ▼                     ▼ ← OPTIONAL: Nice to have

★ = Your priority  |  ★★ = Consider if bugs  |  ★★★ = Future
```

---

## Error Diagnosis Flowchart

```
                       ETL FAILED
                          │
                   ┌──────┴──────┐
                   ▼             ▼
            Check logs       Check DB state
                │                 │
         Can't find       Nothing loaded?
         errors?               │
            │           ┌───────┴─────────┐
            │           ▼                 ▼
            │        Extract    Transform/Load
            │        failed     failed
            │           │           │
            ▼           ▼           ▼
        Services   API problem  Mapping issue
        running?   Credentials? Parameters
            │       Network?    exist?
            │           │           │
            ▼           ▼           ▼
        Restart   Check GCP   Check DB for
        or check  creds.json  param/unit
        logs
```

---

## Timeline: What to Expect

### First Run

```
T+0s    Reset USDA data
        ┌─ 10 seconds
        │
        │
T+10s   Start flow
        ├─ Running...
        │  Extract: 10-30s
        │  Transform: 30-60s
        │  Load: 50-210s (depends on data size)
        │
        ├─ 90-300 seconds total
        │
T+310s  Flow complete
        │
        ├─ 5 seconds
        │
T+315s  Validation script done

        All ✓ = SUCCESS! 🎉
```

---

## Deduplication Explained (Visual)

```
RUN #1: Load 1000 records
    ├─ Extract: 1000 raw records
    ├─ Transform: 950 records (after filtering)
    ├─ Load: 950 new records inserted
    └─ Database now has: 950 records

RUN #2: Run again (retry after bug fix)
    ├─ Extract: 1000 raw records (same API call)
    ├─ Transform: 950 records (same filtered set)
    ├─ Load:
    │   ├─ Level 1: "950 exist in DB, skip"
    │   ├─ Level 2: "Already seen in this batch, skip"
    │   ├─ Level 3: "ON CONFLICT, skip"
    │   └─ Insert: 0 new records
    └─ Database still has: 950 records (no duplicates!)

RESULT: Safe to retry! Dedup prevents duplicate keys.
```

---

## Command Quick Reference (Visual)

```
┌────────────────────────────────────────────────┐
│ BEFORE TESTING                                 │
├────────────────────────────────────────────────┤
│ pixi run service-status     → Check services  │
│ pixi run start-services     → Start if needed │
└────────────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────┐
│ RESET DATA (first run only)                    │
├────────────────────────────────────────────────┤
│ psql ... -f scripts/reset_usda_data.sql       │
└────────────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────┐
│ RUN THE FLOW                                   │
├────────────────────────────────────────────────┤
│ pixi run python -m                             │
│   src.ca_biositing.pipeline.flows.usda_etl   │
└────────────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────┐
│ VALIDATE SUCCESS                               │
├────────────────────────────────────────────────┤
│ psql ... -f scripts/validate_usda_load.sql    │
│ (checks: counts, linkage, integrity, tracking)│
└────────────────────────────────────────────────┘
              │
              ▼
        ✅ ALL DONE!
```

---

## File Organization

```
ca-biositing/
│
├─ src/ca_biositing/pipeline/
│  ├─ flows/
│  │  └─ usda_etl.py ← PRODUCTION CODE (orchestration)
│  │
│  ├─ etl/
│  │  ├─ extract/
│  │  │  └─ usda_census_survey.py ← PRODUCTION CODE (extract)
│  │  ├─ transform/usda/
│  │  │  └─ usda_census_survey.py ← PRODUCTION CODE (transform)
│  │  └─ load/usda/
│  │     └─ usda_census_survey.py ← PRODUCTION CODE (load)
│  │
│  └─ tests/
│     └─ test_usda_etl.py ← UNIT TESTS (optional)
│
├─ scripts/
│  ├─ reset_usda_data.sql ← USE THIS TO RESET
│  └─ validate_usda_load.sql ← USE THIS TO VALIDATE
│
├─ TESTING_RESOURCES_SUMMARY.md ← YOU ARE HERE
├─ HOW_TO_TEST_USDA_ETL.md ← START HERE
├─ QUICK_TEST_REFERENCE.md ← COPY-PASTE COMMANDS
├─ TESTING_AND_RESET_GUIDE.md ← DETAILED (10 parts)
└─ PRODUCTION_CODE_VERIFICATION.md ← PROOF OF CORRECTNESS
```

---

## One-Page Testing Cheatsheet

```
┌─────────────────────────────────────────────┐
│           USDA ETL TESTING CHEATSHEET        │
├─────────────────────────────────────────────┤
│                                             │
│  1. Check Services Running:                 │
│     pixi run service-status                 │
│                                             │
│  2. Reset USDA Data (first time only):     │
│     psql ... -f scripts/reset_usda_data.sql │
│                                             │
│  3. Run Flow:                               │
│     pixi run python -m \                    │
│       src.ca_biositing.pipeline.flows \    │
│       .usda_etl                             │
│                                             │
│  4. Validate:                               │
│     psql ... -f scripts/validate_usda_load  │
│                                             │
│  5. If Failed: Check logs                   │
│     pixi run service-logs                   │
│                                             │
│  KEY FACTS:                                 │
│  ✓ Keep services running (don't teardown)  │
│  ✓ 3-level dedup = safe to retry           │
│  ✓ Reset data only, not services           │
│  ✓ Takes 2-6 minutes per run               │
│  ✓ No duplicates possible                  │
│                                             │
└─────────────────────────────────────────────┘
```

---

**For more details, see:**

- **HOW_TO_TEST_USDA_ETL.md** (best starting point)
- **QUICK_TEST_REFERENCE.md** (commands)
- **TESTING_AND_RESET_GUIDE.md** (deep dive)
