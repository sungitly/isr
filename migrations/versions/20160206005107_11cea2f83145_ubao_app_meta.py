"""
add ubao app meta data and reload crmmgmt app meta

Revision ID: 11cea2f83145
Revises: c2683bbe96f
Create Date: 2016-02-06 00:51:07.814190

"""

# revision identifiers, used by Alembic.
revision = '11cea2f83145'
down_revision = 'c2683bbe96f'
branch_labels = None
depends_on = None


def upgrade():
    from application.nutils.csvloader import reload_table_from_csv
    from application.models.appmeta import AppMeta
    reload_table_from_csv(AppMeta.__tablename__, 'data/app.csv', filters={'name': 'crmmgmt'})
    reload_table_from_csv(AppMeta.__tablename__, 'data/app.csv', filters={'name': 'ubao-ios'})
    reload_table_from_csv(AppMeta.__tablename__, 'data/app.csv', filters={'name': 'ubao-droid'})


def downgrade():
    pass
