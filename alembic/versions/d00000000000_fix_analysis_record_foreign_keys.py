"""Fix foreign key constraints for analysis record tables

Analysis record tables (proximate_record, ultimate_record, compositional_record,
etc.) had FK constraints pointing to 'data_source' instead of 'dataset'.
This migration corrects those constraints.

Revision ID: d00000000000
Revises: a10000000000
Create Date: 2026-01-29 21:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd00000000000'
down_revision: Union[str, Sequence[str], None] = 'a10000000000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix all analysis record FK constraints to point to 'dataset'."""
    tables = [
        'proximate_record',
        'ultimate_record',
        'compositional_record',
        'aim1_record_base',
        'aim2_record_base',
        'autoclave_record',
        'calorimetry_record',
        'fermentation_record',
        'ftnir_record',
        'gasification_record',
        'icp_record',
        'pretreatment_record',
        'rgb_record',
        'xrd_record',
        'xrf_record'
    ]

    for table_name in tables:
        # Drop old FK pointing to data_source
        try:
            op.drop_constraint(
                f'{table_name}_dataset_id_fkey',
                table_name,
                type_='foreignkey'
            )
        except:
            pass

        # Create new FK pointing to dataset
        op.create_foreign_key(
            f'{table_name}_dataset_id_fkey',
            table_name,
            'dataset',
            ['dataset_id'],
            ['id']
        )


def downgrade() -> None:
    """Revert to old FK constraints pointing to 'data_source'."""
    tables = [
        'proximate_record',
        'ultimate_record',
        'compositional_record',
        'aim1_record_base',
        'aim2_record_base',
        'autoclave_record',
        'calorimetry_record',
        'fermentation_record',
        'ftnir_record',
        'gasification_record',
        'icp_record',
        'pretreatment_record',
        'rgb_record',
        'xrd_record',
        'xrf_record'
    ]

    for table_name in tables:
        # Drop new FK
        try:
            op.drop_constraint(
                f'{table_name}_dataset_id_fkey',
                table_name,
                type_='foreignkey'
            )
        except:
            pass

        # Restore old FK pointing to data_source
        op.create_foreign_key(
            f'{table_name}_dataset_id_fkey',
            table_name,
            'data_source',
            ['dataset_id'],
            ['id']
        )
