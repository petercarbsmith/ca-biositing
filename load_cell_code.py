print("="*80)
print("USDA DATA LOAD - Extract → Transform → Load")
print("="*80)

from sqlalchemy import text, insert
from datetime import datetime, timezone
from ca_biositing.datamodels.schemas.generated.ca_biositing import (
    UsdaCensusRecord,
    UsdaSurveyRecord,
    Observation
)

# Get current timestamp for all records
now = datetime.now(timezone.utc)

# ============================================================================
# STEP 1: Load existing records from DATABASE (bypassing session cache)
# ============================================================================
print("\n📦 STEP 1: Load existing records from database...")
existing_census_keys = set()
existing_survey_keys = set()
record_id_map = {}

with engine.connect() as conn:
    result = conn.execute(text("SELECT id, geoid, year, commodity_code FROM usda_census_record"))
    for row in result:
        key = (row[1], row[2], row[3], 'CENSUS')
        existing_census_keys.add(key)
        record_id_map[key] = row[0]

    result = conn.execute(text("SELECT id, geoid, year, commodity_code FROM usda_survey_record"))
    for row in result:
        key = (row[1], row[2], row[3], 'SURVEY')
        existing_survey_keys.add(key)
        record_id_map[key] = row[0]

print(f"  ✓ Found {len(existing_census_keys)} census records")
print(f"  ✓ Found {len(existing_survey_keys)} survey records")

# ============================================================================
# STEP 2: Separate new vs existing records & prepare for insert
# ============================================================================
print(f"\n📋 STEP 2: Prepare new records for insertion...")
census_data = transformed_data[transformed_data['source_type'] == 'CENSUS'].copy()
survey_data = transformed_data[transformed_data['source_type'] == 'SURVEY'].copy()

new_census = []
skip_census = 0
for _, row in census_data.iterrows():
    key = (str(row['geoid']).strip(), int(row['year']), int(row['commodity_code']), 'CENSUS')
    if key not in existing_census_keys:
        new_census.append({
            'geoid': str(row['geoid']).strip(),
            'year': int(row['year']),
            'commodity_code': int(row['commodity_code']),
            'source_reference': str(row.get('source_reference', '')),
            'dataset_id': None,
            'etl_run_id': None,
            'lineage_group_id': None,
            'created_at': now,
            'updated_at': now
        })
    else:
        skip_census += 1

new_survey = []
skip_survey = 0
for _, row in survey_data.iterrows():
    key = (str(row['geoid']).strip(), int(row['year']), int(row['commodity_code']), 'SURVEY')
    if key not in existing_survey_keys:
        new_survey.append({
            'geoid': str(row['geoid']).strip(),
            'year': int(row['year']),
            'commodity_code': int(row['commodity_code']),
            'survey_program_id': None,
            'survey_period': row.get('survey_period'),
            'reference_month': row.get('reference_month'),
            'seasonal_flag': None,
            'note': str(row.get('source_reference', '')),
            'dataset_id': None,
            'etl_run_id': None,
            'lineage_group_id': None,
            'created_at': now,
            'updated_at': now
        })
    else:
        skip_survey += 1

print(f"  Census: {len(new_census)} new, {skip_census} already exist")
print(f"  Survey: {len(new_survey)} new, {skip_survey} already exist")

# ============================================================================
# STEP 3: Insert new census and survey records
# ============================================================================
print(f"\n💾 STEP 3: Insert new records...")
inserted_census = 0
inserted_survey = 0

if new_census:
    census_table = UsdaCensusRecord.__table__
    with engine.begin() as conn:
        result = conn.execute(insert(census_table), new_census)
        inserted_census = result.rowcount
    print(f"  ✅ Inserted {inserted_census} census records")

if new_survey:
    survey_table = UsdaSurveyRecord.__table__
    with engine.begin() as conn:
        result = conn.execute(insert(survey_table), new_survey)
        inserted_survey = result.rowcount
    print(f"  ✅ Inserted {inserted_survey} survey records")

# ============================================================================
# STEP 4: Update record_id_map with newly inserted records
# ============================================================================
if new_census or new_survey:
    print(f"\n🔄 STEP 4: Update record ID mapping...")
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, geoid, year, commodity_code FROM usda_census_record
            WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '1 minute'
        """))
        new_count = 0
        for row in result:
            key = (row[1], row[2], row[3], 'CENSUS')
            if key not in record_id_map:
                record_id_map[key] = row[0]
                new_count += 1
        if new_count > 0:
            print(f"  ✓ Added {new_count} new census record IDs to map")

# ============================================================================
# STEP 5: Prepare observations (will use census/survey record IDs)
# ============================================================================
print(f"\n📊 STEP 5: Prepare observations...")
obs_records = []
for _, row in transformed_data.iterrows():
    geoid_val = str(row['geoid']).strip()
    year_val = int(row['year'])
    commodity_val = int(row['commodity_code'])
    source_type = row['source_type']

    key = (geoid_val, year_val, commodity_val, source_type)
    record_id = record_id_map.get(key)

    if record_id is None:
        continue  # Skip if parent record doesn't exist

    obs_records.append({
        'record_id': record_id,
        'record_type': row['record_type'],
        'parameter_id': int(row['parameter_id']),
        'unit_id': int(row['unit_id']),
        'value_numeric': row['value_numeric'] if not pd.isna(row['value_numeric']) else None,
        'value_text': str(row['value_text']),
        'cv_pct': row['cv_pct'] if not pd.isna(row['cv_pct']) else None,
        'dataset_id': None,
        'etl_run_id': None,
        'lineage_group_id': None,
        'created_at': now,
        'updated_at': now
    })

print(f"  Prepared {len(obs_records)} observations")

# ============================================================================
# STEP 6: Insert observations
# ============================================================================
print(f"\n💾 STEP 6: Insert observations...")
obs_inserted = 0
if obs_records:
    observation_table = Observation.__table__
    with engine.begin() as conn:
        result = conn.execute(insert(observation_table), obs_records)
        obs_inserted = result.rowcount
    print(f"  ✅ Inserted {obs_inserted} observations")

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print(f"\n" + "="*80)
print(f"✅ LOAD COMPLETE")
print(f"="*80)
print(f"Census Records:    {inserted_census} inserted, {skip_census} skipped")
print(f"Survey Records:    {inserted_survey} inserted, {skip_survey} skipped")
print(f"Observations:      {obs_inserted} inserted")
print(f"="*80)
