# USDA NASS API Template Guide

## Overview

A production-ready, configuration-driven template for querying USDA NASS
agricultural data and preparing it for database ingestion. **No code
modifications needed** - adjust only the configuration section.

## Quick Start

1. Open [USDA_Ingestion_Testing.ipynb](USDA_Ingestion_Testing.ipynb)
2. Navigate to **"Production-Ready API Template"** section
3. Modify configuration (SELECTED_STATISTICS, COUNTIES_TO_QUERY, YEAR)
4. Run the cell
5. Use output DataFrame for pipeline tasks

## Configuration Options

### Statistics Selection

```python
SELECTED_STATISTICS = ['YIELD']  # Default

# Available options:
# - 'AREA HARVESTED'  (unit: ACRES)
# - 'PRODUCTION'      (unit: TONS)
# - 'YIELD'          (unit: TONS)
# - 'PRICE RECEIVED' (unit: DOLLARS)

# Query multiple statistics:
SELECTED_STATISTICS = ['YIELD', 'PRODUCTION', 'AREA HARVESTED']
```

### County Selection

```python
COUNTIES_TO_QUERY = {
    'San Joaquin': {'fips': '06077', 'nass_code': '077'},
    'Merced': {'fips': '06047', 'nass_code': '047'},
}

# Add new counties (need FIPS and NASS codes):
# FIPS format: 06XXX (e.g., 06077)
# NASS format: XXX (e.g., 077)
# Mapping: drop '06' prefix from FIPS to get NASS code
```

### Year Selection

```python
YEAR = 2022  # Default (complete data)

# Notes:
# - 2022: Complete data available
# - 2023: May have incomplete data
# - Earlier years: Depends on NASS availability
```

## Output Schema

The template produces a DataFrame with these columns:

| Column        | Type  | Description         | Example         |
| ------------- | ----- | ------------------- | --------------- |
| `commodity`   | str   | Commodity name      | "WHEAT"         |
| `year`        | int   | Data year           | 2022            |
| `county`      | str   | County name         | "San Joaquin"   |
| `fips`        | str   | County FIPS code    | "06077"         |
| `statistic`   | str   | Measurement type    | "YIELD"         |
| `unit`        | str   | Unit for statistic  | "TONS"          |
| `observation` | float | Numeric value       | 42.5            |
| `description` | str   | Human-readable desc | "YIELD in TONS" |

**Note**: `created_at` and `updated_at` are NOT included in output. They're
added automatically by the database ORM during load.

## Timestamp Strategy

### Decision: Add at Load Time (NOT Extract Time)

**Why this approach?**

1. **Follows existing patterns**: Google Sheets extraction in the project uses
   this same strategy
2. **Cleaner code**: Extract focuses on data retrieval, not metadata
3. **Single source of truth**: Database controls insertion timestamp
4. **Audit trail**: Timestamp reflects actual DB insert time

**How it works:**

```
Extract → Raw Data (no timestamps)
   ↓
Transform → Transformed Data (no timestamps)
   ↓
Load → ORM Objects (timestamps added automatically by SQLAlchemy)
   ↓
Database (records with created_at/updated_at populated)
```

### Implementation

In the load task, don't set timestamps manually:

```python
# ❌ DON'T do this:
record.created_at = datetime.now()
record.updated_at = datetime.now()

# ✅ DO this:
record = UsdaCensusRecord(
    geoid=row['geoid'],
    commodity_code=row['commodity_code'],
    year=row['year'],
    # ... other fields ...
    # No created_at or updated_at - let ORM handle it
)
session.add(record)
session.commit()  # Timestamps auto-generated here
```

### If You Need Explicit Timestamps

If the database doesn't auto-generate timestamps, update the LinkML schema:

```yaml
# In src/ca_biositing/datamodels/.../linkml/modules/core/base_entity.yaml

created_at:
  range: datetime
  description: Timestamp when record was created
  sql_type: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

Then regenerate migrations:

```bash
pixi run update-schema -m "Add timestamp defaults to BaseEntity"
pixi run migrate
```

## Usage Examples

### Example 1: Query Multiple Statistics

```python
# Configuration:
SELECTED_STATISTICS = ['YIELD', 'PRODUCTION', 'AREA HARVESTED']

# Result: DataFrame with 3x rows per commodity
# (one row per statistic per county)
```

### Example 2: Query All 3 Priority Counties

```python
# San Joaquin Valley (3 main counties)
COUNTIES_TO_QUERY = {
    'San Joaquin': {'fips': '06077', 'nass_code': '077'},
    'Stanislaus': {'fips': '06099', 'nass_code': '099'},  # Large dataset, may timeout
    'Merced': {'fips': '06047', 'nass_code': '047'},
}

# Note: Stanislaus can timeout due to large dataset size. If timeout occurs,
# increase max_retries or timeout value, or query counties individually.

# Template automatically iterates both counties
```

### Example 3: Query Different Year

```python
YEAR = 2023  # or 2021, 2020, etc.

# Template queries the specified year
```

### Example 4: Use Template Output in Pipeline

```python
# After running template, use output_df:

# 1. (Optional) Filter to specific commodities:
filtered = output_df[output_df['commodity'].isin(['WHEAT', 'CORN'])]

# 2. (Optional) Transform/clean:
# transformed = transform(filtered)

# 3. Load to database:
from ca_biositing.pipeline.etl.load.usda.usda_census_survey import load
success = load(filtered)
# Records now in database with auto-generated timestamps
```

## Statistics & Units Mapping

Hard-coded pairs (from NASS API):

| Statistic      | Unit    | Typical Values      |
| -------------- | ------- | ------------------- |
| AREA HARVESTED | ACRES   | 100,000 - 1,000,000 |
| PRODUCTION     | TONS    | 50,000 - 500,000    |
| YIELD          | TONS    | 10 - 100            |
| PRICE RECEIVED | DOLLARS | 5 - 20              |

Default statistic: **YIELD** (can be changed in template)

## Troubleshooting

| Problem                | Solution                                                                                                                                      |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| "API key not found"    | Ensure `usda_api_key` is set from `.env` file (see Setup cell)                                                                                |
| "No records retrieved" | Check YEAR (2023 may be incomplete), verify county codes, check API key quota                                                                 |
| "Timeout errors"       | Stanislaus county has large dataset. Try: 1) Increase `max_retries` to 5, 2) Increase `timeout` to 60 seconds, 3) Query counties individually |
| "County code mismatch" | Verify NASS code is correct (3-digit, e.g., '077' not '06077')                                                                                |
| "Commodity not found"  | Check `get_mapped_commodity_ids()` to see available mappings                                                                                  |

## Data Quality Notes

### 2022 Data (Used as Default)

- **Coverage**: Complete for most California commodities and counties
- **Reliability**: High (published data)
- **Commodity count**: 186 unique commodities in San Joaquin Valley
- **Records retrieved**: ~4,500 records for 2 counties

### 2023 Data

- **Status**: Likely incomplete (preliminary estimates)
- **Use case**: Only if current-year estimates needed
- **Recommendation**: Use 2022 for analysis, 2023 for trends only

## Next Steps

1. **Basic Query**: Run template with default settings to validate API access
2. **Multi-County**: Add Stanislaus County (066099 FIPS, 099 NASS) to county
   list
3. **Full Pipeline**: Integrate output_df into transform and load tasks
4. **Production Deployment**: Move template logic to `usda_nass_to_pandas.py`
   extract task

## Related Files

- Template location:
  [USDA_Ingestion_Testing.ipynb](USDA_Ingestion_Testing.ipynb) (Section:
  "Production-Ready API Template")
- Extract task:
  `src/ca_biositing/pipeline/ca_biositing/pipeline/etl/extract/usda_census_survey.py`
- Load task:
  `src/ca_biositing/pipeline/ca_biositing/pipeline/etl/load/usda/usda_census_survey.py`
- Database models:
  `src/ca_biositing/datamodels/ca_biositing/datamodels/schemas/generated/ca_biositing.py`
  (UsdaCensusRecord class)
- Commodity mapping: Database function `get_mapped_commodity_ids()`

## Summary

- ✅ Configuration-driven (no code changes needed)
- ✅ Handles county iteration and code conversion
- ✅ Transforms NASS API responses to standard schema
- ✅ Includes error handling and retry logic
- ✅ Timestamps managed by ORM at load time
- ✅ Ready for production pipeline integration
