"""add table hwjd_account to store hwjd oa accounts

Revision ID: 31f0f0f984fe
Revises: 1c422fc68bc7
Create Date: 2016-08-24 14:16:15.578635

"""

# revision identifiers, used by Alembic.
revision = '31f0f0f984fe'
down_revision = '1c422fc68bc7'
branch_labels = None
depends_on = None

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.create_table('hwjd_account',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('store_id', sa.BigInteger(), nullable=True),
                    sa.Column('name', sa.String(length=200), nullable=True),
                    sa.Column('org_code', sa.String(length=50), nullable=True),
                    sa.Column('user_code', sa.String(length=50), nullable=True),
                    sa.Column('password', sa.String(length=50), nullable=True),
                    sa.Column('active', sa.Boolean(), nullable=True, server_default='1'),
                    sa.Column('make', sa.String(length=200), nullable=True),
                    sa.Column('models', sa.String(length=1000), nullable=True),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('store_id')
                    )


def downgrade():
    op.drop_table('hwjd_account')
