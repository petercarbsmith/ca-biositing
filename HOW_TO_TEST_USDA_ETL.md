# Testing USDA ETL - Complete Guide

## Quick Answer

**Q: Should I teardown services before running the flow locally?**

**A: NO ❌ - Keep services running!**

- Services provide infrastructure (Postgres, Prefect)
- Just reset the USDA data, not the services
- Faster turnaround (no 30-second startup)
- Easier debugging (can inspect DB between runs)

---

## Testing Strategy (Simple Version)

### Test Levels (Pyramid)

```
                    ▲ E2E
                   ╱│╲ (Full flow, real DB)
                  ╱ │ ╲
                 ╱  │  ╲
                ╱   │   ╲ Integration
               ╱    │    ╲ (transform + load tasks)
              ╱     │     ╲
             ╱      │      ╲
            ▼───────┴───────▼
            Unit Tests
        (Functions, mock data)
```

**Test Recommended for Your Situation:**

1. ✅ **E2E Test** (most important - you have production code)
2. ✅ **Manual validation** (quick SQL checks)
3. ⚠️ **Unit tests** (nice to have, not critical)

---

## Your Testing Workflow

### Scenario 1: First Time Testing Production Code

```bash
# 1. Check services are running
pixi run service-status
# If not: pixi run start-services

# 2. Reset USDA data (clean slate)
psql postgresql://user:password@localhost:5432/ca_biositing \
  -f scripts/reset_usda_data.sql

# 3. Run the production flow
pixi run python -m src.ca_biositing.pipeline.flows.usda_etl

# 4. Validate success
psql postgresql://user:password@localhost:5432/ca_biositing \
  -f scripts/validate_usda_load.sql

# Expected output:
#   Census records > 0 ✓
#   Survey records > 0 ✓
#   Observations > 0 ✓
#   100% linked to datasets ✓
```

**Time: 2-5 minutes** (depending on data volume)

### Scenario 2: Testing After a Code Fix

```bash
# Option A: Keep existing data (dedup prevents duplicates)
pixi run python -m src.ca_biositing.pipeline.flows.usda_etl
psql ... -f scripts/validate_usda_load.sql

# Option B: Fresh start (cleaner comparison)
psql ... -f scripts/reset_usda_data.sql
pixi run python -m src.ca_biositing.pipeline.flows.usda_etl
psql ... -f scripts/validate_usda_load.sql
```

**Time: 2-5 minutes per iteration**

### Scenario 3: Something Went Wrong

```bash
# Step 1: Check what happened
psql postgresql://user:password@localhost:5432/ca_biositing
SELECT COUNT(*) FROM usda_census_record;
SELECT COUNT(*) FROM observation
  WHERE record_type = 'usda_census_record';

# Step 2: Check logs
pixi run service-logs | grep -i "error\|usda" | tail -20

# Step 3: If failed partway through (no worries!)
# Your code has 3-level dedup - safe to just re-run:
pixi run python -m src.ca_biositing.pipeline.flows.usda_etl

# Step 4: If you want fresh start:
psql ... -f scripts/reset_usda_data.sql
pixi run python -m src.ca_biositing.pipeline.flows.usda_etl
```

**Time: 5-10 minutes depending on issue**

---

## What Each File Does

### Scripts Created

| File                             | Purpose                               | When to Run          |
| -------------------------------- | ------------------------------------- | -------------------- |
| `scripts/reset_usda_data.sql`    | Deletes USDA data, keeps other data   | Before each test run |
| `scripts/validate_usda_load.sql` | Checks load success (counts, linkage) | After ETL completes  |

### Documentation

| File                              | Purpose                     |
| --------------------------------- | --------------------------- |
| `TESTING_AND_RESET_GUIDE.md`      | Full guide (parts 1-10)     |
| `QUICK_TEST_REFERENCE.md`         | Quick command reference     |
| `PRODUCTION_CODE_VERIFICATION.md` | Proof code matches notebook |

### Test Code

| File                             | Purpose             |
| -------------------------------- | ------------------- |
| `src/.../tests/test_usda_etl.py` | Unit test templates |

---

## Key Decisions Explained

### Decision 1: Keep Services Running

| Approach                | Pros                               | Cons                            |
| ----------------------- | ---------------------------------- | ------------------------------- |
| **Keep running ✅**     | Fast, debuggable, same as notebook | Disk usage (minor)              |
| **Teardown every time** | Clean slate, minimal resources     | Slow startup (30 sec each time) |

**Winner: Keep running** - faster iteration during development

### Decision 2: Reset vs Keep Data

**Your situation:** Notebook already loaded data

| Approach                 | Pros                          | Cons             | Use When                               |
| ------------------------ | ----------------------------- | ---------------- | -------------------------------------- |
| **Reset each time**      | Clean comparison, predictable | Takes 10 seconds | First test, comparing results          |
| **Keep data**            | Fast, accumulates all tests   | Dedup needed     | Iterating on fixes, safe because dedup |
| **Both (separate runs)** | Best of both                  | More manual work | Full validation                        |

**Recommendation: Reset first run, then keep data for subsequent runs** (dedup
makes it safe)

### Decision 3: Service Teardown

**When to teardown:**

- Database corruption suspected
- Services completely hung
- Docker networking issues
- Testing in isolated environment

**When NOT to teardown:**

- Normal test iterations (99% of time)
- Partial load/failure (dedup handles it)
- Debugging (need to inspect DB state)
- Time matters (startup takes 30 seconds)

---

## Success Criteria

### ✅ Your Test Passed If...

```sql
-- Run this query after ETL:
SELECT
  (SELECT COUNT(*) FROM usda_census_record) > 0 as has_census,
  (SELECT COUNT(*) FROM usda_survey_record) > 0 as has_survey,
  (SELECT COUNT(*) FROM observation
   WHERE record_type IN ('usda_census_record', 'usda_survey_record')) > 0 as has_observations,
  (SELECT COUNT(*) FROM usda_census_record WHERE dataset_id IS NULL) = 0 as all_census_linked,
  (SELECT COUNT(*) FROM usda_survey_record WHERE dataset_id IS NULL) = 0 as all_survey_linked,
  (SELECT COUNT(DISTINCT etl_run_id) FROM observation
   WHERE record_type IN ('usda_census_record', 'usda_survey_record')) > 0 as has_etl_tracking;
```

All should return `true`

### ❌ Test Failed If...

| Sign                  | What to Check                             |
| --------------------- | ----------------------------------------- |
| Counts = 0            | Is extract working? API credentials?      |
| 100% dropped rows     | Mapping working? Parameters/units exist?  |
| dataset_id is NULL    | Dataset creation failed                   |
| Observations = 0      | Value conversion failing?                 |
| Orphaned observations | Missing parent records (shouldn't happen) |

---

## Commands You'll Use

### Essential Commands

```bash
# Start services (if needed)
pixi run start-services

# Check status
pixi run service-status

# Reset USDA data
psql postgresql://user:password@localhost:5432/ca_biositing \
  -f scripts/reset_usda_data.sql

# Run flow locally
pixi run python -m src.ca_biositing.pipeline.flows.usda_etl

# Validate success
psql postgresql://user:password@localhost:5432/ca_biositing \
  -f scripts/validate_usda_load.sql

# Check logs
pixi run service-logs
```

### Optional Commands

```bash
# Run unit tests
pixi run pytest src/ca_biositing/pipeline/tests/test_usda_etl.py -v

# Quick status (one line)
psql postgresql://user:password@localhost:5432/ca_biositing \
  -c "SELECT COUNT(*) FROM usda_census_record;"

# Connect to database
psql postgresql://user:password@localhost:5432/ca_biositing

# Rebuild services (only if broken)
pixi run docker compose down
pixi run docker compose up -d
```

---

## Typical Test Run Timeline

### First Run (Fresh Start)

```
Check services         5 sec
Reset data             10 sec
Run ETL              90-300 sec (depends on data size)
Validate             5 sec
─────────────────────────
Total:              2-6 minutes
```

### Subsequent Runs (With Fix)

```
Run ETL              90-300 sec
Validate             5 sec
─────────────────────────
Total:              2-6 minutes
(Skips reset - dedup handles duplicates)
```

---

## If Something Goes Wrong

### "Services not running"

```bash
pixi run start-services
# Wait ~10 seconds for Postgres to start
```

### "Can't connect to database"

```bash
# Check Postgres is actually running
pixi run service-status

# Check logs
pixi run service-logs | grep postgres | tail -10
```

### "Module not found: ca_biositing"

```bash
# WRONG:
python src/ca_biositing/pipeline/flows/usda_etl.py

# RIGHT:
pixi run python -m src.ca_biositing.pipeline.flows.usda_etl
```

### "No raw data to transform"

```bash
# Check:
# 1. Is GCP credentials.json in repo root?
# 2. Can you access USDA API?
# 3. Is extract() working?
```

### "All records dropped"

```bash
# Check:
# 1. Are parameters/units in DB?
#    SELECT COUNT(*) FROM parameter;
# 2. Is commodity mapping working?
#    SELECT COUNT(*) FROM usda_commodity;
# 3. Is value conversion to numeric working?
#    (Check logs for specific field errors)
```

### "Partial load - want to retry"

```bash
# DON'T PANIC - 3-level dedup prevents duplicates!
# Just run again:
pixi run python -m src.ca_biositing.pipeline.flows.usda_etl

# Or reset and retry:
psql ... -f scripts/reset_usda_data.sql
pixi run python -m src.ca_biositing.pipeline.flows.usda_etl
```

---

## FAQ

**Q: Will running the flow twice create duplicates?** A: No! 3-level
deduplication prevents duplicates:

- Level 1: Skip if exists in DB
- Level 2: Skip if seen in batch
- Level 3: PostgreSQL ON CONFLICT

**Q: Should I reset services between runs?** A: No - keep them running. Just
reset USDA data if needed.

**Q: Can I inspect the data while flow is running?** A: Yes! Open another
terminal and query the DB while it runs.

**Q: How long should the flow take?** A: 2-6 minutes depending on data volume.
If > 10 min, probably hung.

**Q: Should I commit test data to Git?** A: No - SQL scripts go in Git, data
stays in Postgres only.

**Q: Can I run tests in Prefect UI instead?** A: Yes - deploy to Prefect and
trigger from UI. Same code, easier to monitor.

---

## Next Steps

1. **Try it:** Follow "Scenario 1" above (first time)
2. **Validate:** Run validation script, check counts
3. **Inspect:** Open Data Wrangler to view USDA tables
4. **Debug:** If issues, check specific logs
5. **Iterate:** Make code fixes and re-run

**Questions?** Check [TESTING_AND_RESET_GUIDE.md](TESTING_AND_RESET_GUIDE.md)
for detailed info.
