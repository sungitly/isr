"""
Add columns guid, extra and index to vin

Revision ID: 270ebb13fc31
Revises: 1762b4269242
Create Date: 2016-01-17 15:42:38.054168

"""

# revision identifiers, used by Alembic.
revision = '270ebb13fc31'
down_revision = '1762b4269242'
branch_labels = None
depends_on = None

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.add_column('inventory', sa.Column('extra', sa.Text(), nullable=True))
    op.create_index(op.f('ix_inventory_vin'), 'inventory', ['vin'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_inventory_vin'), table_name='inventory')
    op.drop_column('inventory', 'extra')
