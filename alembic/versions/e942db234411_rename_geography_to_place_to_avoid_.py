"""Rename Geography to Place to avoid PostGIS conflict

Revision ID: e942db234411
Revises: 51167f08e5d5
Create Date: 2026-01-20 15:03:40.212613

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e942db234411'
down_revision: Union[str, Sequence[str], None] = '51167f08e5d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Note: This migration assumes geography_table exists, but it doesn't
    # in the current schema. Making this a no-op since the tables don't exist
    # and the schema has moved past this state.
    pass


def downgrade() -> None:
    """Downgrade schema."""
    op.create_table('geography_table',
    sa.Column('geoid', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('state_name', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('state_fips', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('county_name', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('county_fips', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('region_name', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('agg_level_desc', sa.TEXT(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('geoid')
    )
    op.execute("INSERT INTO geography_table SELECT * FROM place")
    op.drop_constraint('location_address_geography_id_fkey', 'location_address', type_='foreignkey')
    op.create_foreign_key('location_address_geography_id_fkey', 'location_address', 'geography_table', ['geography_id'], ['geoid'])
    op.drop_table('place')
