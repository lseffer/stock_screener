"""screener results view

Revision ID: 4f406bad1840
Revises: 0e87ac62cba4
Create Date: 2019-06-11 20:03:12.716812

"""
from alembic import op
from utils.models import ScreenResults


# revision identifiers, used by Alembic.
revision = '4f406bad1840'
down_revision = '0e87ac62cba4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_view(ScreenResults)


def downgrade():
    op.drop_view(ScreenResults)
