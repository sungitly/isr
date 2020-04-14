""" create hwjd_lookup to store hw lookups

Revision ID: 4646b694b761
Revises: 5cf3facb96f
Create Date: 2016-08-24 17:44:53.197055

"""

# revision identifiers, used by Alembic.
revision = '4646b694b761'
down_revision = '5cf3facb96f'
branch_labels = None
depends_on = None

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.create_table('hwjd_lookup',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('type', sa.String(length=50), nullable=True),
                    sa.Column('code', sa.String(length=50), nullable=True),
                    sa.Column('name', sa.String(length=200), nullable=True),
                    sa.Column('make', sa.String(length=100), nullable=True),
                    sa.Column('model', sa.String(length=100), nullable=True),
                    sa.Column('extra', sa.String(length=200), nullable=True),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('code')
                    )


def downgrade():
    op.drop_table('hwjd_lookup')
