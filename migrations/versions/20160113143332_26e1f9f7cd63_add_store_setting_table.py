"""
Add store_setting table

Revision ID: 26e1f9f7cd63
Revises: 1c44d9b6b58e
Create Date: 2016-01-13 14:33:32.915830

"""

# revision identifiers, used by Alembic.
revision = '26e1f9f7cd63'
down_revision = '1c44d9b6b58e'
branch_labels = None
depends_on = None

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.create_table('store_setting',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('created_on', sa.DateTime(), nullable=True),
                    sa.Column('updated_on', sa.DateTime(), nullable=True),
                    sa.Column('created_by', sa.String(length=50), nullable=True),
                    sa.Column('updated_by', sa.String(length=50), nullable=True),
                    sa.Column('store_id', sa.BigInteger(), nullable=False),
                    sa.Column('type', sa.String(length=50), nullable=True),
                    sa.Column('value', sa.Text(), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_store_setting_store_id'), 'store_setting', ['store_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_store_setting_store_id'), table_name='store_setting')
    op.drop_table('store_setting')
