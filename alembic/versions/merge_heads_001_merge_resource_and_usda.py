"""Merge migration heads: resource pipeline and USDA commodity mapper

Revision ID: merge_heads_001
Revises: 92c712030571, 807417ade886
Create Date: 2026-01-23 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'merge_heads_001'
down_revision: Union[str, Sequence[str], None] = ('92c712030571', '807417ade886')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # This is a merge migration - no actual changes needed
    # It just combines the two migration branches
    pass


def downgrade() -> None:
    # No changes to downgrade
    pass
