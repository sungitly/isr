"""load hwjd oa accounts

Revision ID: 5cf3facb96f
Revises: 31f0f0f984fe
Create Date: 2016-08-24 14:26:30.028801

"""

# revision identifiers, used by Alembic.
from application.nutils.csvloader import reload_table_from_csv

revision = '5cf3facb96f'
down_revision = '31f0f0f984fe'
branch_labels = None
depends_on = None


def upgrade():
    from application.models.hwaccount import HwjdAccount
    reload_table_from_csv(HwjdAccount.__tablename__, 'data/hwjd/accounts.csv')


def downgrade():
    pass
