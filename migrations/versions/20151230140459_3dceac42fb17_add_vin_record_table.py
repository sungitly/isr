""" Add vin_record table

Revision ID: 3dceac42fb17
Revises: 19575cd37849
Create Date: 2015-12-30 14:04:59.132782

"""

# revision identifiers, used by Alembic.
revision = '3dceac42fb17'
down_revision = '19575cd37849'
branch_labels = None
depends_on = None

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.create_table('vin_record',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('vin', sa.String(length=20), nullable=True),
                    sa.Column('source', sa.String(length=20), nullable=True),
                    sa.Column('year', sa.Integer(), nullable=True),
                    sa.Column('make', sa.String(length=50), nullable=True),
                    sa.Column('model', sa.String(length=100), nullable=True),
                    sa.Column('extra', sa.Text(), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_vin_record_vin'), 'vin_record', ['vin'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_vin_record_vin'), table_name='vin_record')
    op.drop_table('vin_record')
