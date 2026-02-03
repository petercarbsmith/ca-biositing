# Plan: LandIQ County and FIPS Integration

This plan outlines the steps to integrate county names and FIPS codes (GEOIDs)
into the LandIQ data pipeline, ensuring the data is correctly cleaned and linked
for downstream analytics.

## 1. Schema Updates (LinkML)

- **LandIQ Record**: Add a `county` slot to the `LandiqRecord` class in
  `src/ca_biositing/datamodels/ca_biositing/datamodels/linkml/modules/external_data/landiq_record.yaml`.
- **Polygon**: Ensure the `geoid` slot in `Polygon` is correctly defined to
  store the 5-digit FIPS code.

## 2. Database Migration

- Run `pixi run update-schema -m "Add county to landiq_record"` to generate
  SQLAlchemy models and Alembic migrations.
- Apply the migration using `pixi run migrate`.

## 3. ETL Pipeline Enhancements

### LandIQ Record ETL

- Modify the transformation logic to extract the `county` field from the source
  data.
- Implement cleaning logic to convert county names to lowercase before
  upserting.
- Update the loader to handle the new `county` column.

### FIPS/GEOID Integration

- Create a lookup utility or table that maps California county names to their
  5-digit FIPS codes (GEOID).
- Modify the `Polygon` ETL to:
  - Retrieve the county name associated with the polygon (either from the LandIQ
    record or spatial join).
  - Look up the corresponding FIPS code.
  - Populate the `geoid` column in the `polygon` table.

## 4. Testing and Validation

- Create unit tests for the new cleaning and lookup logic.
- Run the updated ETL pipeline on a subset of data.
- Verify that:
  - `landiq_record.county` contains lowercase county names.
  - `polygon.geoid` contains the correct 5-digit FIPS codes.
  - Joins between `landiq_record`, `polygon`, and `place` (once populated) work
    as expected.

## 5. Materialized View (Resume)

- Once the underlying data is correctly populated, proceed with creating the
  `landiq_tileset` materialized view in the `ca_biositing` schema.
