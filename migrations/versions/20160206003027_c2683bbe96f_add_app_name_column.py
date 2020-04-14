"""
drop app_id column of release history table. add app_name column instead.

Revision ID: c2683bbe96f
Revises: 548dc4c2c25d
Create Date: 2016-02-06 00:30:27.232876

"""

# revision identifiers, used by Alembic.
from alembic.ddl import mysql

revision = 'c2683bbe96f'
down_revision = '548dc4c2c25d'
branch_labels = None
depends_on = None

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.add_column('release_history', sa.Column('app_name', sa.String(length=100), nullable=False))

    # data migration
    op.execute('UPDATE release_history r INNER JOIN app a ON a.id = r.app_id SET r.app_name = a.name;')
    op.drop_column('release_history', 'app_id')


def downgrade():
    op.add_column('release_history',
                  sa.Column('app_id', mysql.BIGINT(display_width=20), autoincrement=False, nullable=True))
    # data migration
    op.execute('UPDATE release_history r INNER JOIN app a ON a.name = r.app_name SET r.app_id = a.id;')
    op.drop_column('release_history', 'app_name')
