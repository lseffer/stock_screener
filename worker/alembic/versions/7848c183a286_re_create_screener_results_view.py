"""re-create screener results view

Revision ID: 7848c183a286
Revises: 4f406bad1840
Create Date: 2019-12-08 10:46:02.145678

"""
from alembic import op
from utils.models import ScreenResults


# revision identifiers, used by Alembic.
revision = '7848c183a286'
down_revision = '4f406bad1840'
branch_labels = None
depends_on = None


def upgrade():
    op.create_view(ScreenResults)


def downgrade():
    op.drop_view(ScreenResults)
