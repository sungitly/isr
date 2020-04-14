"""
Create ISR inventory table

Revision ID: 1c44d9b6b58e
Revises: 3dceac42fb17
Create Date: 2016-01-13 13:37:40.658935

"""

# revision identifiers, used by Alembic.
revision = '1c44d9b6b58e'
down_revision = '3dceac42fb17'
branch_labels = None
depends_on = None

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.create_table('inventory',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('created_on', sa.DateTime(), nullable=True),
                    sa.Column('updated_on', sa.DateTime(), nullable=True),
                    sa.Column('created_by', sa.String(length=50), nullable=True),
                    sa.Column('updated_by', sa.String(length=50), nullable=True),
                    sa.Column('store_id', sa.BigInteger(), nullable=False),
                    sa.Column('vin', sa.String(length=50), nullable=True),
                    sa.Column('car_brand', sa.String(length=20), nullable=True),
                    sa.Column('car_class', sa.String(length=200), nullable=True),
                    sa.Column('car_type', sa.String(length=200), nullable=True),
                    sa.Column('car_subtype', sa.String(length=200), nullable=True),
                    sa.Column('acc_info', sa.String(length=200), nullable=True),
                    sa.Column('acc_price', sa.Numeric(precision=12, scale=2), nullable=True),
                    sa.Column('color_name', sa.String(length=50), nullable=True),
                    sa.Column('color_attribute', sa.String(length=50), nullable=True),
                    sa.Column('source', sa.String(length=50), nullable=True),
                    sa.Column('in_price', sa.Numeric(precision=12, scale=2), nullable=True),
                    sa.Column('inv_status', sa.String(length=50), nullable=True),
                    sa.Column('out_factory_date', sa.Date(), nullable=True),
                    sa.Column('stockin_date', sa.Date(), nullable=True),
                    sa.Column('mrsp', sa.Numeric(precision=12, scale=2), nullable=True),
                    sa.Column('rebate_amt', sa.Numeric(precision=12, scale=2), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_inventory_store_id'), 'inventory', ['store_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_inventory_store_id'), table_name='inventory')
    op.drop_table('inventory')
