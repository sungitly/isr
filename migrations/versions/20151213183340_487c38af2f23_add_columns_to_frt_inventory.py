"""empty message

Revision ID: 487c38af2f23
Revises: 1630d134738d
Create Date: 2015-12-13 18:33:40.180887

"""

# revision identifiers, used by Alembic.
revision = '487c38af2f23'
down_revision = 'e78cd9cb708'
branch_labels = None
depends_on = None

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.add_column('frt_inventory', sa.Column('stockage_cat', sa.String(length=50), nullable=True))
    op.add_column('frt_inventory', sa.Column('shared', sa.String(length=50), nullable=True))


def downgrade():
    op.drop_column('frt_inventory', 'stockage_cat')
    op.drop_column('frt_inventory', 'shared')
