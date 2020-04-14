"""Add download_website to app table

Revision ID: 531314db4378
Revises: 11cea2f83145
Create Date: 2016-02-29 12:38:07.028373

"""

# revision identifiers, used by Alembic.
revision = '531314db4378'
down_revision = '11cea2f83145'
branch_labels = None
depends_on = None

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.add_column('app', sa.Column('download_website', sa.String(length=500), nullable=True))


def downgrade():
    op.drop_column('app', 'download_website')
