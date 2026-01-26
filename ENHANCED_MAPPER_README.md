# Enhanced USDA Commodity Mapper

**Status**: Ready for use after Tuesday meeting **Purpose**: Interactive tool to
map your project resources to USDA commodity codes

## What It Does

Implements the exact workflow you described:

1. ✅ **Fetches ALL commodities** available for California from NASS API (not
   hardcoded)
2. ✅ **Gets your resources** from `primary_ag_product` and `resource` tables
3. ✅ **Auto-matches clear matches** (>90% string similarity)
4. ✅ **Interactive fuzzy matching** - presents 1-5 candidates, you pick best
5. ✅ **Leaves unmapped if no match** - no forced mappings
6. ✅ **Saves to database** in `resource_usda_commodity_map` table

## Quick Start

```bash
# Complete workflow (all steps at once):
python enhanced_commodity_mapper.py --full-workflow

# Or run steps individually:
python enhanced_commodity_mapper.py --fetch-ca-commodities  # Step 1: Get CA commodities
python enhanced_commodity_mapper.py --auto-match            # Step 2: Auto-match >90%
python enhanced_commodity_mapper.py --review                # Step 3: Interactive review
python enhanced_commodity_mapper.py --save                  # Step 4: Save to database
```

## Example Interactive Session

```
STEP 4: Interactive Review of Fuzzy Matches
================================================================================

You have 12 resources with fuzzy matches to review.

For each resource, select the best USDA commodity match:
  - Enter 1-5 to select a candidate
  - Enter 'n' to skip (no good match)
  - Enter 'q' to quit and save progress

[1/12] Resource: 'Alfalfa' (primary_ag_product)
--------------------------------------------------------------------------------
  [1] HAY, ALFALFA (code: 18199999) - 95% match
      Description: HAY, ALFALFA - ACRES HARVESTED
  [2] ALFALFA SEED (code: 18299999) - 78% match
  [3] HAY (code: 18100000) - 65% match
  [4] HAY, (EXCL ALFALFA) (code: 18199200) - 62% match
  [5] FORAGE (code: 28100000) - 60% match

  [n] No good match - leave unmapped

Your selection (1-5, n, or q): 1
  ✓ Matched: Alfalfa → HAY, ALFALFA

[2/12] Resource: 'Biomass Sorghum' (primary_ag_product)
--------------------------------------------------------------------------------
  [1] SORGHUM (code: 16100000) - 75% match
  [2] SORGHUM, GRAIN (code: 16199199) - 72% match
  [3] SORGHUM, SILAGE (code: 16199299) - 70% match
  [4] SUGARCANE (code: 16500000) - 45% match
  [5] RICE (code: 14100000) - 40% match

  [n] No good match - leave unmapped

Your selection (1-5, n, or q): 1
  ✓ Matched: Biomass Sorghum → SORGHUM

...

✓ Review complete! 10 total matches approved.

STEP 5: Saving Approved Mappings to Database
================================================================================

Saving 10 mappings to database...
  ✓ Saved: Alfalfa → HAY, ALFALFA (USER_APPROVED)
  ✓ Saved: Biomass Sorghum → SORGHUM (USER_APPROVED)
  ...

✓ Saved 10 new mappings
```

## What Gets Saved to Database

Each approved mapping creates:

```sql
INSERT INTO resource_usda_commodity_map (
    primary_ag_product_id,   -- Your crop ID
    usda_commodity_id,       -- USDA commodity ID
    match_tier,              -- 'AUTO_MATCH' or 'USER_APPROVED'
    note,                    -- Details: similarity score, matching method
    created_at,
    updated_at
) VALUES (...);
```

Also ensures USDA commodity exists in `usda_commodity` table:

```sql
INSERT INTO usda_commodity (
    name,           -- e.g., 'HAY, ALFALFA'
    usda_code,      -- e.g., '18199999'
    usda_source,    -- 'NASS'
    created_at,
    updated_at
) VALUES (...);
```

## Files Created

Script creates cache directory: `.cache/`

- `ca_usda_commodities.json` - All CA commodities from NASS (refreshable)
- `pending_matches.json` - Fuzzy matches awaiting review
- `approved_matches.json` - User-approved matches ready to save

**Note**: These are intermediate files. Final data goes in database.

## How It Works

### Auto-Match (>90% similarity)

```python
# Example:
Your Resource: "Corn"
USDA Commodity: "CORN"
Similarity: 100%
→ AUTO-MATCHED ✓

Your Resource: "Almonds"
USDA Commodity: "ALMONDS"
Similarity: 100%
→ AUTO-MATCHED ✓
```

### Fuzzy Match (60-90% similarity)

```python
# Example:
Your Resource: "Sweet Corn"
Candidates:
  1. CORN, SWEET (95% match) ← Best
  2. CORN (75% match)
  3. CORN, GRAIN (70% match)
You select: 1
→ USER-APPROVED ✓

Your Resource: "Tree Nuts"
Candidates:
  1. ALMONDS (55% match)
  2. WALNUTS (53% match)
  3. PECANS (52% match)
All scores too low
You select: n (no match)
→ LEFT UNMAPPED (OK - can map later)
```

## Reference

USDA Commodity Codes Official List:
https://www.nass.usda.gov/Data_and_Statistics/County_Data_Files/Frequently_Asked_Questions/commcodes.php

## When to Run This

**After Tuesday meeting** when you have:

- ✓ Proven extract→transform→load pipeline working
- ✓ Time to review matches carefully (1-2 hours)
- ✓ Clarity on which crops your team needs

**Benefits of waiting**:

- Less pressure = better match quality
- Can ask coworkers which crops matter most
- Pipeline already working with current mappings

## Estimated Time

- **Fetch commodities**: ~2 min (run once, then cached)
- **Auto-match**: ~1 min (script does this automatically)
- **Interactive review**: ~1-2 hours (depends on # of resources)
  - Average: ~2-3 min per resource
  - 30-40 resources = ~1.5 hours
- **Save to database**: ~1 min

**Total**: ~2-3 hours for complete commodity mapping

## Technical Details

**Dependencies**: Uses existing codebase

- `USDA_NASS_API_KEY` from `.env`
- Database connection from `DATABASE_URL`
- NASS API for live commodity data

**Safe to re-run**:

- Checks for existing mappings before inserting
- Won't duplicate entries
- Can run `--review` multiple times (progress saved)

**Match Quality Tracking**:

- `AUTO_MATCH`: >90% similarity, no human review
- `USER_APPROVED`: 60-90% similarity, human selected best match
- `match_tier` saved in database for audit trail

## Questions?

See [SATURDAY_WORK_PLAN.md](SATURDAY_WORK_PLAN.md) for integration with overall
timeline.
