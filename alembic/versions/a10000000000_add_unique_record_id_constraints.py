"""Add unique record_id constraints for upsert operations

These constraints enable ON CONFLICT (record_id) DO UPDATE patterns
used throughout the ETL pipeline for idempotent inserts.

Revision ID: a10000000000
Revises: merge_heads_001
Create Date: 2026-01-28 19:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a10000000000'
down_revision: Union[str, Sequence[str], None] = 'merge_heads_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add UNIQUE constraints on record_id for all *_record tables."""
    # observation table - use composite key since multiple observations per record_id
    # (one for each parameter_id + unit_id combination)
    op.create_unique_constraint(
        'uq_observation_record_parameter_unit',
        'observation',
        ['record_id', 'record_type', 'parameter_id', 'unit_id']
    )

    # aim1_record_base table
    op.create_unique_constraint(
        'uq_aim1_record_base_record_id',
        'aim1_record_base',
        ['record_id']
    )

    # aim2_record_base table
    op.create_unique_constraint(
        'uq_aim2_record_base_record_id',
        'aim2_record_base',
        ['record_id']
    )

    # autoclave_record table
    op.create_unique_constraint(
        'uq_autoclave_record_record_id',
        'autoclave_record',
        ['record_id']
    )

    # calorimetry_record table
    op.create_unique_constraint(
        'uq_calorimetry_record_record_id',
        'calorimetry_record',
        ['record_id']
    )

    # compositional_record table
    op.create_unique_constraint(
        'uq_compositional_record_record_id',
        'compositional_record',
        ['record_id']
    )

    # fermentation_record table
    op.create_unique_constraint(
        'uq_fermentation_record_record_id',
        'fermentation_record',
        ['record_id']
    )

    # ftnir_record table
    op.create_unique_constraint(
        'uq_ftnir_record_record_id',
        'ftnir_record',
        ['record_id']
    )

    # gasification_record table
    op.create_unique_constraint(
        'uq_gasification_record_record_id',
        'gasification_record',
        ['record_id']
    )

    # icp_record table
    op.create_unique_constraint(
        'uq_icp_record_record_id',
        'icp_record',
        ['record_id']
    )

    # pretreatment_record table
    op.create_unique_constraint(
        'uq_pretreatment_record_record_id',
        'pretreatment_record',
        ['record_id']
    )

    # proximate_record table
    op.create_unique_constraint(
        'uq_proximate_record_record_id',
        'proximate_record',
        ['record_id']
    )

    # rgb_record table
    op.create_unique_constraint(
        'uq_rgb_record_record_id',
        'rgb_record',
        ['record_id']
    )

    # ultimate_record table
    op.create_unique_constraint(
        'uq_ultimate_record_record_id',
        'ultimate_record',
        ['record_id']
    )

    # xrd_record table
    op.create_unique_constraint(
        'uq_xrd_record_record_id',
        'xrd_record',
        ['record_id']
    )

    # xrf_record table
    op.create_unique_constraint(
        'uq_xrf_record_record_id',
        'xrf_record',
        ['record_id']
    )


def downgrade() -> None:
    """Remove unique record_id constraints."""
    op.drop_constraint('uq_xrf_record_record_id', 'xrf_record', type_='unique')
    op.drop_constraint('uq_xrd_record_record_id', 'xrd_record', type_='unique')
    op.drop_constraint('uq_ultimate_record_record_id', 'ultimate_record', type_='unique')
    op.drop_constraint('uq_rgb_record_record_id', 'rgb_record', type_='unique')
    op.drop_constraint('uq_proximate_record_record_id', 'proximate_record', type_='unique')
    op.drop_constraint('uq_pretreatment_record_record_id', 'pretreatment_record', type_='unique')
    op.drop_constraint('uq_icp_record_record_id', 'icp_record', type_='unique')
    op.drop_constraint('uq_gasification_record_record_id', 'gasification_record', type_='unique')
    op.drop_constraint('uq_ftnir_record_record_id', 'ftnir_record', type_='unique')
    op.drop_constraint('uq_fermentation_record_record_id', 'fermentation_record', type_='unique')
    op.drop_constraint('uq_compositional_record_record_id', 'compositional_record', type_='unique')
    op.drop_constraint('uq_calorimetry_record_record_id', 'calorimetry_record', type_='unique')
    op.drop_constraint('uq_autoclave_record_record_id', 'autoclave_record', type_='unique')
    op.drop_constraint('uq_aim2_record_base_record_id', 'aim2_record_base', type_='unique')
    op.drop_constraint('uq_aim1_record_base_record_id', 'aim1_record_base', type_='unique')
    op.drop_constraint('uq_observation_record_parameter_unit', 'observation', type_='unique')
