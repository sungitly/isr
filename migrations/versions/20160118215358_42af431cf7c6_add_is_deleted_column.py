"""
add is_deleted column to inventory table

Revision ID: 42af431cf7c6
Revises: 270ebb13fc31
Create Date: 2016-01-18 21:53:58.378220

"""

# revision identifiers, used by Alembic.
revision = '42af431cf7c6'
down_revision = '270ebb13fc31'
branch_labels = None
depends_on = None

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.add_column('inventory', sa.Column('is_deleted', sa.Boolean(), nullable=True))


def downgrade():
    op.drop_column('inventory', 'is_deleted')
