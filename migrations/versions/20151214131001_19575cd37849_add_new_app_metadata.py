# -*- coding: utf-8 -*-
"""add new app metadata

Revision ID: 19575cd37849
Revises: 487c38af2f23
Create Date: 2015-12-14 13:10:01.492391

"""

# revision identifiers, used by Alembic.

revision = '19575cd37849'
down_revision = '487c38af2f23'
branch_labels = None
depends_on = None


def upgrade():
    from application.nutils.csvloader import reload_table_from_csv
    from application.models.appmeta import AppMeta
    reload_table_from_csv(AppMeta.__tablename__, 'data/app.csv', filters={'name': 'crmmgmt'})


def downgrade():
    pass
