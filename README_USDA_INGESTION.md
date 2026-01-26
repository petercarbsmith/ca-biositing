# USDA Ingestion Pipeline - Master Summary & Next Steps

**Last Updated**: January 23, 2026 **Status**: Phase planning complete,
implementation starting **Timeline**: Saturday work (extract), Monday work
(transform/load), Tuesday 2pm delivery

---

## What We've Accomplished (This Session)

### ✅ Phase 1: Template & Architecture

- ✅ Created production-ready USDA NASS API template with 8-column output schema
- ✅ Analyzed timestamp strategy (added at DB insert time via ORM, not in
  extract/transform)
- ✅ Fixed FIPS code bug (prepend STATE_FIPS for 5-digit codes)
- ✅ Added Stanislaus county back with timeout troubleshooting

### ✅ Phase 2: Data Model Analysis

- ✅ Analyzed UsdaCensusRecord table requirements
- ✅ Analyzed Observation table requirements
- ✅ Mapped API output → database schema relationships
- ✅ Identified Parameter/Unit table needs
- ✅ Created comprehensive transform design document

### ✅ Phase 3: Commodity Mapping Tool

- ✅ Created `enhanced_commodity_mapper.py` with live API integration
- ✅ Implemented auto-match (>90%) and interactive fuzzy matching (60-90%)
- ✅ Added database integration with audit trail
- ✅ **Key decision**: Commodity list managed separately, ingestion doesn't
  touch it

### ✅ Phase 4: Documentation & Planning

- ✅ Created work plan for Saturday/Monday (SATURDAY_WORK_PLAN.md)
- ✅ Updated all USDA documentation for consistency
- ✅ Created API template guide (USDA_API_TEMPLATE_GUIDE.md)
- ✅ Created enhanced mapper guide (ENHANCED_MAPPER_README.md)

---

## What's Next (Starting Saturday)

| Phase       | Task                                                               | Timeline        | Blocker?             |
| ----------- | ------------------------------------------------------------------ | --------------- | -------------------- |
| **NOW**     | Create/update Parameter & Unit tables with proper fields           | Before Saturday | ⚠️ YES               |
| Saturday    | Test extract with API template (1-2 counties)                      | 30-45 min       | No                   |
| Saturday    | Inspect raw data from extract                                      | 30 min          | No                   |
| Saturday    | Research transform requirements (understand Observation structure) | 1 hour          | No                   |
| Monday      | Implement transform logic (map commodities, parameters, units)     | 45-60 min       | Depends on Saturday  |
| Monday      | Implement load logic (insert to both tables)                       | 45-60 min       | Depends on transform |
| Monday      | End-to-end test with all 3 counties + all 4 statistics             | 30 min          | Depends on load      |
| Tuesday 2pm | **DELIVERY**: Working pipeline with data in database               | ✅ Goal         |                      |
| After Tue   | Run enhanced_commodity_mapper for comprehensive mapping            | 2-3 hours       | No                   |

---

## Critical Implementation Detail: Parameter & Unit Tables

**⚠️ ACTION NEEDED BEFORE SATURDAY:**

The transform needs Parameter and Unit tables with proper schema. Currently:

- Parameter table may exist but might lack `abbreviation` field
- Unit table may exist but might lack `abbreviation` field

**Required fields**:

```sql
parameter (id, name, description, standard_unit_id, calculated, created_at, updated_at)
unit (id, name, description, abbreviation, created_at, updated_at)

-- Then seed with:
INSERT INTO parameter (name, description, calculated) VALUES
  ('YIELD', 'Yield per unit area', false),
  ('PRODUCTION', 'Total production quantity', false),
  ('AREA HARVESTED', 'Area harvested', false),
  ('PRICE RECEIVED', 'Price received by farmer', false);

INSERT INTO unit (name, description, abbreviation) VALUES
  ('BUSHELS', 'US bushels', 'BU'),
  ('TONS', 'Short tons (US)', 'T'),
  ('ACRES', 'US acres', 'AC'),
  ('DOLLARS', 'US dollars', '$');
```

**Action**: Check if tables exist and have needed fields. If not, create LinkML
schema updates + migration.

---

## Data Flow (Reference)

```
API Query Template (USDA_Ingestion_Testing.ipynb, cell 12)
    ↓ output_df (8 columns: commodity, year, county, fips, statistic, unit, observation, description)
    ↓
EXTRACT → raw_data DataFrame (ready for transform)
    ↓
TRANSFORM (map names to IDs, create both record types)
    ├→ UsdaCensusRecord records (geoid, commodity_code, year)
    └→ Observation records (parameter_id, value, unit_id)
    ↓
LOAD (insert to both tables with FK relationships)
    ↓
Database (fully normalized measurement data)
```

---

## File Organization: Keep vs Delete

### 🟢 KEEP These (Active Reference)

1. **[USDA_TRANSFORM_DESIGN.md](USDA_TRANSFORM_DESIGN.md)** ← **START HERE FOR
   IMPLEMENTATION**
   - Complete data model mapping
   - Transform logic flow
   - Q&A and decisions
   - Implementation checklist
   - Schema requirements

2. **[SATURDAY_WORK_PLAN.md](SATURDAY_WORK_PLAN.md)** ← **START HERE FOR
   TIMING**
   - Detailed timeline for this weekend
   - Task breakdowns with time estimates
   - Troubleshooting tips
   - Reference data locations

3. **[ENHANCED_MAPPER_README.md](ENHANCED_MAPPER_README.md)**
   - How to use the commodity mapper tool
   - Keep for after Tuesday when running mapper

### 🟡 KEEP (Reference Only - Don't Update)

4. **[USDA_API_TEMPLATE_GUIDE.md](USDA_API_TEMPLATE_GUIDE.md)**
   - Reference for API template usage
   - Configuration options
   - Troubleshooting

### 🔴 CAN DELETE (Consolidated Into This Document)

- TEMPLATE_IMPLEMENTATION_SUMMARY.md (info is in USDA_API_TEMPLATE_GUIDE.md now)
- USDA_MATCHER_GUIDE.md (updated version exists, matcher is separate tool)
- DOCUMENTATION_CONSISTENCY_UPDATE.md (task complete, info already in other
  docs)

---

## Quick Reference: Key Files

| File                 | Purpose                         | Location                                 |
| -------------------- | ------------------------------- | ---------------------------------------- |
| **API Template**     | Query USDA NASS API with config | USDA_Ingestion_Testing.ipynb, cell 12    |
| **Transform Design** | What to do in transform step    | USDA_TRANSFORM_DESIGN.md                 |
| **Commodity Mapper** | Map commodities to USDA codes   | enhanced_commodity_mapper.py (after Tue) |
| **Work Timeline**    | When to run what                | SATURDAY_WORK_PLAN.md                    |
| **Notebook**         | All testing cells               | USDA_Ingestion_Testing.ipynb             |

---

## Notebook Cells: What to Run

| Cell # | Name                   | Purpose                                      | Status                          |
| ------ | ---------------------- | -------------------------------------------- | ------------------------------- |
| 1-7    | Setup & Config         | Environment, DB connection, commodity mapper | ✅ Works                        |
| 8-11   | Debug & API Test       | Debug inspect, API exploration               | ✅ Works                        |
| 12     | **API Template**       | Extract via USDA NASS                        | 🟡 Ready (test Saturday)        |
| 13     | Data Prep              | Convert template output to raw_data          | 🟡 Ready (test Saturday)        |
| 14     | **Transform Analysis** | Shows what needs to happen                   | 🟡 Ready (shows requirements)   |
| 15     | Load (placeholder)     | Will insert records                          | 🔴 Needs update after transform |
| 16+    | End-to-end tests       | Full flow verification                       | 🔴 After load is ready          |

---

## One-Sentence Summaries (No Time to Read?)

| Doc                       | TL;DR                                                                                          |
| ------------------------- | ---------------------------------------------------------------------------------------------- |
| USDA_TRANSFORM_DESIGN.md  | One API row → two DB records (UsdaCensusRecord + Observation), requires Parameter/Unit lookups |
| SATURDAY_WORK_PLAN.md     | Saturday: test extract, Monday: build transform/load, Tuesday: deliver                         |
| ENHANCED_MAPPER_README.md | Run this after Tuesday to map all commodities from API                                         |

---

## Troubleshooting Quick Links

**Problem**: "Commodity not mapped" → See USDA_TRANSFORM_DESIGN.md Q2, or run
enhanced_commodity_mapper.py

**Problem**: "Parameter/Unit not found" → See blockers section above, need to
create/seed tables first

**Problem**: "Transform not working" → See USDA_TRANSFORM_DESIGN.md
implementation checklist

**Problem**: "Stanislaus county timing out" → See SATURDAY_WORK_PLAN.md
"Troubleshooting" section

---

## Next Action

1. **TODAY (Before leaving)**: Check if Parameter/Unit tables exist with needed
   fields
2. **Tomorrow**: Follow SATURDAY_WORK_PLAN.md timeline
3. **When blocked**: Check USDA_TRANSFORM_DESIGN.md Q&A section

**You've got this!** 🚀
