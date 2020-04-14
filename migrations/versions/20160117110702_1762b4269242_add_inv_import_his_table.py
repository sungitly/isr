"""
Add inv_import_his table

Revision ID: 1762b4269242
Revises: 26e1f9f7cd63
Create Date: 2016-01-17 11:07:02.980284

"""

# revision identifiers, used by Alembic.
revision = '1762b4269242'
down_revision = '26e1f9f7cd63'
branch_labels = None
depends_on = None

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.create_table('inv_import_his',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('created_on', sa.DateTime(), nullable=True),
                    sa.Column('created_by', sa.String(length=50), nullable=True),
                    sa.Column('origin_file', sa.String(length=100), nullable=True),
                    sa.Column('import_file', sa.String(length=500), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )


def downgrade():
    op.drop_table('inv_import_his')
