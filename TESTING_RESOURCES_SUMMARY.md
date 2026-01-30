# Testing Resources Summary

## Your Question Answered ✅

**Q: How should I test this code? And how should I reset if it fails? Should I
teardown services?**

**A:**

1. ✅ **Don't teardown services** - keep Postgres/Prefect running
2. ✅ **Reset USDA data** - use SQL script between runs
3. ✅ **Use 3-level dedup** - safe to retry if it fails partially
4. ✅ **Run locally** - with
   `pixi run python -m src.ca_biositing.pipeline.flows.usda_etl`

---

## Files Created For You

### Quick Start Documents

| Document                       | Purpose              | Read This If...                |
| ------------------------------ | -------------------- | ------------------------------ |
| **HOW_TO_TEST_USDA_ETL.md**    | Executive summary    | You want the TL;DR version     |
| **QUICK_TEST_REFERENCE.md**    | Copy-paste commands  | You just want commands to run  |
| **TESTING_AND_RESET_GUIDE.md** | Deep dive (10 parts) | You need detailed explanations |

### Helper Scripts

| Script                             | Purpose                           | Run With                                 |
| ---------------------------------- | --------------------------------- | ---------------------------------------- |
| **scripts/reset_usda_data.sql**    | Clean USDA data (keep other data) | `psql -f scripts/reset_usda_data.sql`    |
| **scripts/validate_usda_load.sql** | Check success with 8 validations  | `psql -f scripts/validate_usda_load.sql` |

### Test Code

| File                               | Purpose             | Run With                              |
| ---------------------------------- | ------------------- | ------------------------------------- |
| **src/.../tests/test_usda_etl.py** | Unit test templates | `pixi run pytest test_usda_etl.py -v` |

### Supporting Documentation

| Document                            | Purpose                                      |
| ----------------------------------- | -------------------------------------------- |
| **PRODUCTION_CODE_VERIFICATION.md** | Proves code matches notebook (100% coverage) |

---

## The Simple Testing Process

```bash
# 1. Make sure services are running
pixi run service-status

# 2. Reset USDA data (first run only)
psql postgresql://user:password@localhost:5432/ca_biositing -f scripts/reset_usda_data.sql

# 3. Run your production flow
pixi run python -m src.ca_biositing.pipeline.flows.usda_etl

# 4. Check if it worked
psql postgresql://user:password@localhost:5432/ca_biositing -f scripts/validate_usda_load.sql
```

**That's it!** Takes 2-6 minutes total.

---

## Key Concepts

### Why Keep Services Running?

```
❌ Teardown every time         ✅ Keep running
─────────────────────────────────────────────────
30 sec startup overhead        No startup delay
Manual migrations needed       Instant access
Lose inspection capability     Can debug live
Hard to track changes          Easy comparison
```

### Why 3-Level Dedup is Your Friend

```
Level 1: DB check     ← Prevents re-inserting existing records
Level 2: Batch check  ← Prevents duplicates within this load
Level 3: SQL check    ← Catches edge cases at insert time
───────────────────────────────────────────────────────────
Result: Safe to retry even if load fails partway
```

### When to Reset Data

```
RESET if:                          KEEP if:
├─ First test run                 ├─ Code fix, retry
├─ Want clean comparison          ├─ Want to accumulate data
├─ Database looks corrupt         ├─ Dedup prevents duplicates
└─ Starting fresh test cycle      └─ Time matters (skip reset)
```

---

## Success Checklist

After flow completes, verify:

- [ ] Census records > 0
- [ ] Survey records > 0
- [ ] Observations > 0
- [ ] 100% of records have dataset_id
- [ ] 0 orphaned observations (referential integrity OK)
- [ ] etl_run_id is tracked
- [ ] No errors in Prefect logs

Run validation script to check all of these automatically.

---

## If It Fails

| Symptom           | Likely Cause            | Fix                         |
| ----------------- | ----------------------- | --------------------------- |
| Can't connect     | Services not running    | `pixi run start-services`   |
| Module errors     | Wrong Python run method | Use `pixi run python -m`    |
| No data extracted | Extract not working     | Check GCP credentials       |
| All rows dropped  | Mapping failed          | Check if params/units exist |
| Partial load      | ETL interrupted         | Dedup = safe to retry       |
| DB corrupted      | Unknown error           | Reset USDA data, try again  |

---

## What NOT To Do

❌ **Don't:**

```bash
# Don't run Python directly
python src/ca_biositing/pipeline/flows/usda_etl.py

# Don't teardown services each time
pixi run docker compose down

# Don't manually delete all data if partial load
# (dedup handles it safely)

# Don't try to import modules at module level
# (use lazy imports - production code does this)
```

✅ **Do:**

```bash
# Run with Pixi
pixi run python -m src.ca_biositing.pipeline.flows.usda_etl

# Keep services running between tests
# (just reset data)

# Use the dedup - it's safe to retry
# (just re-run the same command)

# Inspect with SQL scripts provided
# (they have all needed queries)
```

---

## Command Reference

### Essentials

```bash
pixi run service-status           # Check if Postgres/Prefect running
pixi run start-services           # Start Postgres and Prefect
pixi run python -m src.ca_biositing.pipeline.flows.usda_etl  # Run flow
psql ... -f scripts/reset_usda_data.sql      # Reset data
psql ... -f scripts/validate_usda_load.sql   # Check success
pixi run service-logs             # View logs
```

### Optional

```bash
pixi run pytest test_usda_etl.py -v          # Run unit tests
psql ... -c "SELECT COUNT(*) FROM usda_census_record;"  # Quick count
docker compose logs postgres                 # Docker logs
pixi run docker compose down                 # Stop services (rarely needed)
```

---

## Estimated Timings

| Task            | Time                              |
| --------------- | --------------------------------- |
| Reset USDA data | 10 sec                            |
| Run full ETL    | 90-300 sec (depends on data size) |
| Validate        | 5 sec                             |
| Debug / inspect | 5-10 min                          |
| **Full cycle**  | **2-6 min**                       |

---

## Where To Get Help

### For Command Reference

→ **QUICK_TEST_REFERENCE.md**

### For Detailed Steps

→ **HOW_TO_TEST_USDA_ETL.md**

### For In-Depth Guide

→ **TESTING_AND_RESET_GUIDE.md** (10 comprehensive parts)

### For Code Details

→ **PRODUCTION_CODE_VERIFICATION.md** (detailed coverage analysis)

---

## Next Steps

1. **Read** HOW_TO_TEST_USDA_ETL.md (5 min) - get oriented
2. **Run** the commands in "Scenario 1" - first test
3. **Validate** using the SQL script - confirm success
4. **Debug** if needed using command reference
5. **Iterate** on fixes and re-test

You're all set! 🚀
