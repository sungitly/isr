"""empty message

Revision ID: 318877c78598
Revises: 531314db4378
Create Date: 2016-03-11 11:36:38.242316

"""

# revision identifiers, used by Alembic.
revision = '318877c78598'
down_revision = '531314db4378'
branch_labels = None
depends_on = None


def upgrade():
    from application.nutils.csvloader import reload_table_from_csv
    from application.models.appmeta import AppMeta
    reload_table_from_csv(AppMeta.__tablename__, 'data/app.csv', filters={'name': 'uubao-ios'})
    reload_table_from_csv(AppMeta.__tablename__, 'data/app.csv', filters={'name': 'uubao-droid'})


def downgrade():
    pass
