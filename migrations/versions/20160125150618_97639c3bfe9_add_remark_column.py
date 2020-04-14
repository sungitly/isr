"""add remark column to inventory table

Revision ID: 97639c3bfe9
Revises: 42af431cf7c6
Create Date: 2016-01-25 15:06:18.557828

"""

# revision identifiers, used by Alembic.
revision = '97639c3bfe9'
down_revision = '42af431cf7c6'
branch_labels = None
depends_on = None

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.add_column('inventory', sa.Column('remark', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('inventory', 'remark')
