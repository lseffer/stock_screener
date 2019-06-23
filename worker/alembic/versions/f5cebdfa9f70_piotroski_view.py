"""piotroski view

Revision ID: f5cebdfa9f70
Revises: 00b80735370b
Create Date: 2019-05-05 16:15:14.365580

"""
from alembic import op
from utils.models import PiotroskiScore

# revision identifiers, used by Alembic.
revision = 'f5cebdfa9f70'
down_revision = '00b80735370b'
branch_labels = None
depends_on = None


def upgrade():
    op.create_view(PiotroskiScore)


def downgrade():
    op.drop_view(PiotroskiScore)
