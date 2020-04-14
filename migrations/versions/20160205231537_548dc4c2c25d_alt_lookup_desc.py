"""
Change description column of lookup model as nullable

Revision ID: 548dc4c2c25d
Revises: 97639c3bfe9
Create Date: 2016-02-05 23:15:37.572839

"""

# revision identifiers, used by Alembic.
revision = '548dc4c2c25d'
down_revision = '97639c3bfe9'
branch_labels = None
depends_on = None

from alembic import op
from sqlalchemy.dialects import mysql


def upgrade():
    op.alter_column('lookup', 'description', existing_type=mysql.VARCHAR(length=100), nullable=True)


def downgrade():
    op.alter_column('lookup', 'description', existing_type=mysql.VARCHAR(length=100), nullable=False)
