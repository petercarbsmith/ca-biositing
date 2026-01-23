# USDA Commodity Code Matching Strategy

## Overview

Instead of manually hardcoding commodity codes, we've created an intelligent
matching system that:

1. **Searches** for USDA commodity codes based on your resource/crop names
2. **Presents candidates** for developer review (with fuzzy matching scores)
3. **Saves approved matches** to the database
4. **Supports incremental updates** when new resources are added

## The Process

### Step 1: Initial Search (Search All Resources)

```bash
pixi run python match_usda_commodities.py --search-all
```

This will:

- Query all unique names from `primary_crop` and `resource` tables
- Find matching USDA commodity codes for each name
- Present top 5 matches with similarity scores
- Let you select matches interactively

### Step 2: Review Pending Matches

```bash
pixi run python match_usda_commodities.py --review
```

Shows the file: `.usda_pending_matches.json` with all selected matches.

**Tip:** You can edit this JSON file directly to modify matches before applying.

### Step 3: Apply to Database

```bash
pixi run python match_usda_commodities.py --apply-pending
```

Stores all reviewed matches in `resource_usda_commodity_map`.

### Quick Search (For Individual Crops)

```bash
pixi run python match_usda_commodities.py --search "Alfalfa"
```

Shows top 10 matching USDA codes without going through the full interactive
process.

## Workflow for New Resources

When you add new crops/resources to the database:

```bash
# Search the database again
pixi run python match_usda_commodities.py --search-all

# Review only the new entries in .usda_pending_matches.json
# Edit JSON or run interactive again

# Apply to database
pixi run python match_usda_commodities.py --apply-pending
```

## Current Commodity Database

The matcher includes 40+ common agricultural commodities with fuzzy matching on:

- Commodity descriptions (e.g., "Corn For Grain")
- Common names (e.g., "corn", "grain corn", "field corn")

Supported commodities include:

- **Grains**: Corn, Wheat, Barley, Soybeans
- **Nuts**: Almonds, Walnuts, Pecans, Pistachios
- **Vegetables**: Tomatoes, Peppers, Lettuce, Broccoli, etc.
- **Fruits**: Apples, Grapes, Cherries, Strawberries, etc.
- **Other**: Alfalfa, Hay, Citrus, Beans, etc.

## Design Advantages

| Aspect                 | Hardcoded Approach         | Matcher Approach            |
| ---------------------- | -------------------------- | --------------------------- |
| **Adding new crops**   | Edit code, reseed database | Run script, review, approve |
| **Scalability**        | Breaks with growth         | Grows with database         |
| **Accuracy**           | Manual, error-prone        | Fuzzy matching + review     |
| **Auditability**       | No record of decisions     | JSON stores methodology     |
| **Team collaboration** | Developer-only             | Any team member can review  |

## Files

- `match_usda_commodities.py` - Main matcher script
- `.usda_pending_matches.json` - Stores pending matches for review (generated)

## Future Improvements

- Load USDA commodity list from API instead of hardcoding
- Store fuzzy match scores in database for audit trail
- Create web UI for match review and approval
- Auto-approve high-confidence matches (>0.95)
- Support batch operations on resource groups
