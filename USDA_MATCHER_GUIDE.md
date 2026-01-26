# USDA Commodity Code Matching Strategy

## Overview

**ENHANCED VERSION NOW AVAILABLE**: `enhanced_commodity_mapper.py`

This enhanced version fetches ALL California commodities from the live NASS API
(not hardcoded) and provides:

1. **Live API integration** - Fetches all CA commodities from NASS QuickStats
   API
2. **Auto-matching** - Automatically approves clear matches (>90% similarity)
3. **Interactive fuzzy matching** - Presents 1-5 candidates for user selection
4. **Quality control** - Option to leave unmapped if no good match exists
5. **Database integration** - Saves to `resource_usda_commodity_map` with audit
   trail

## The Enhanced Process (Recommended)

### Complete Workflow

```bash
# Run entire workflow (fetch → auto-match → review → save)
python enhanced_commodity_mapper.py --full-workflow
```

### Step-by-Step Process

**Step 1: Fetch All CA Commodities from NASS API**

```bash
python enhanced_commodity_mapper.py --fetch-ca-commodities
```

- Queries NASS QuickStats API for all California commodities
- Caches results in `.cache/ca_usda_commodities.json`
- Run once, then reuse cached data (or re-run to refresh)

**Step 2: Auto-Match Clear Matches**

```bash
python enhanced_commodity_mapper.py --auto-match
```

- Automatically matches resources with >90% similarity
- Saves auto-matches to `.cache/approved_matches.json`
- Saves fuzzy matches (60-90%) to `.cache/pending_matches.json` for review

**Step 3: Interactive Review of Fuzzy Matches**

```bash
python enhanced_commodity_mapper.py --review
```

- Shows 1-5 best candidate matches for each resource
- You select best match or skip (no forced mappings)
- Progress saved (can quit and resume with 'q')

Example:

```
[1/12] Resource: 'Alfalfa' (primary_ag_product)
  [1] HAY, ALFALFA (code: 18199999) - 95% match
  [2] ALFALFA SEED (code: 18299999) - 78% match
  [3] HAY (code: 18100000) - 65% match
  [n] No good match - leave unmapped

Your selection (1-3, n, or q): 1
  ✓ Matched: Alfalfa → HAY, ALFALFA
```

**Step 4: Save Approved Mappings to Database**

```bash
python enhanced_commodity_mapper.py --save
```

- Inserts approved mappings into `resource_usda_commodity_map`
- Creates `usda_commodity` entries if needed
- Tracks match quality (AUTO_MATCH vs USER_APPROVED)
- Safe to re-run (checks for existing mappings)

## Workflow for New Resources

When you add new crops/resources to the database:

```bash
# Run full workflow (auto-match + review + save)
python enhanced_commodity_mapper.py --full-workflow

# Or step-by-step:
python enhanced_commodity_mapper.py --auto-match  # Auto-match new resources
python enhanced_commodity_mapper.py --review      # Review fuzzy matches
python enhanced_commodity_mapper.py --save        # Save to database
```

The enhanced mapper automatically detects which resources need mapping and skips
already-mapped resources.

## Enhanced Commodity Database

**Live API Integration:**

The enhanced mapper fetches ALL California commodities directly from the NASS
QuickStats API. As of 2022, this includes:

- **~1,000+ commodity codes** covering all agricultural products tracked in
  California
- **Dynamic updates**: Re-run `--fetch-ca-commodities` to refresh from API
- **No hardcoding required**: All commodities loaded programmatically

**Match Quality Tiers:**

1. **AUTO_MATCH (>90% similarity)**
   - High confidence matches automatically approved
   - Example: "RICE" → "RICE" (100% match)

2. **USER_APPROVED (60-90% similarity)**
   - Fuzzy matches presented for interactive selection
   - Example: "Alfalfa" → "HAY, ALFALFA" (95% match, requires confirmation)

3. **NO_MATCH (<60% similarity)**
   - No good candidates found
   - Resource left unmapped (better than wrong mapping)

**Database Tables:**

- `usda_commodity`: Official USDA commodity codes and names
- `resource_usda_commodity_map`: Links resources to commodity codes with audit
  trail (match_tier, user_notes, timestamps)

## Design Advantages: Enhanced vs Old Approach

| Aspect                 | Old Hardcoded Matcher       | Enhanced API Mapper                  |
| ---------------------- | --------------------------- | ------------------------------------ |
| **Commodity Coverage** | 40+ hardcoded commodities   | 1,000+ from live NASS API            |
| **Adding new crops**   | Run script, review, approve | Run script, auto-match + review      |
| **Scalability**        | Grows with database         | Grows with database AND NASS API     |
| **Accuracy**           | Fuzzy matching + manual     | Tiered: Auto (>90%) + Fuzzy (60-90%) |
| **Auditability**       | JSON stores methodology     | Database stores match tier + notes   |
| **Maintenance**        | Update hardcoded list       | Refresh from API (no code changes)   |
| **Team collaboration** | Any team member can review  | Interactive CLI with progress save   |

## Files

**Enhanced Mapper (Recommended):**

- `enhanced_commodity_mapper.py` - Enhanced mapper with live API integration
- `ENHANCED_MAPPER_README.md` - Complete user guide
- `.cache/ca_usda_commodities.json` - Cached CA commodities from NASS API
- `.cache/pending_matches.json` - Fuzzy matches awaiting user review
- `.cache/approved_matches.json` - Auto-matched and user-approved mappings

**Legacy Matcher (Deprecated):**

- `match_usda_commodities.py` - Old hardcoded matcher (40+ commodities)
- `.usda_pending_matches.json` - Old pending matches format

## Status: Enhanced Features Implemented

**✅ IMPLEMENTED (enhanced_commodity_mapper.py):**

- ✅ Load USDA commodity list from API instead of hardcoding
- ✅ Store match quality tier in database for audit trail (AUTO_MATCH vs
  USER_APPROVED)
- ✅ Auto-approve high-confidence matches (>90% similarity threshold)
- ✅ Interactive CLI for fuzzy match review and approval
- ✅ Progress saving (quit and resume with 'q')

**📋 FUTURE IMPROVEMENTS:**

- Create web UI for match review and approval
- Support batch operations on resource groups
- Add confidence intervals and statistical validation
- Integrate with broader data quality monitoring
