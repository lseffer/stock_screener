"""magic formula view

Revision ID: 0e87ac62cba4
Revises: f5cebdfa9f70
Create Date: 2019-06-11 17:35:08.715102

"""
from alembic import op
from utils.models import MagicFormulaScore


# revision identifiers, used by Alembic.
revision = '0e87ac62cba4'
down_revision = 'f5cebdfa9f70'
branch_labels = None
depends_on = None


def upgrade():
    op.create_view(MagicFormulaScore)


def downgrade():
    op.drop_view(MagicFormulaScore)
