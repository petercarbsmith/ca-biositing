"""Rename primary_crop_id to primary_ag_product_id in resource_usda_commodity_map

Revision ID: fix_col_name_001
Revises: 807417ade886
Create Date: 2026-01-22 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fix_col_name_001'
down_revision = '807417ade886'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename the column to match the schema
    op.alter_column(
        'resource_usda_commodity_map',
        'primary_crop_id',
        new_column_name='primary_ag_product_id',
        existing_type=sa.Integer(),
        existing_nullable=True
    )


def downgrade() -> None:
    # Revert the column name
    op.alter_column(
        'resource_usda_commodity_map',
        'primary_ag_product_id',
        new_column_name='primary_crop_id',
        existing_type=sa.Integer(),
        existing_nullable=True
    )
