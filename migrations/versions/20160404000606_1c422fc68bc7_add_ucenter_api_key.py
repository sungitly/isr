"""
Add API Key for ucenter

Revision ID: 1c422fc68bc7
Revises: 318877c78598
Create Date: 2016-04-04 00:06:06.873700

"""

# revision identifiers, used by Alembic.
revision = '1c422fc68bc7'
down_revision = '318877c78598'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    from application.nutils.csvloader import reload_table_from_csv
    from application.models.appmeta import AppMeta
    reload_table_from_csv(AppMeta.__tablename__, 'data/app.csv', filters={'name': 'ucenter'})


def downgrade():
    pass
