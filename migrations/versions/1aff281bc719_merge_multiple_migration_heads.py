"""merge_multiple_migration_heads

Revision ID: 1aff281bc719
Revises: add_photo_comment, 20251013_profile_pic, f1a2b3c4d5e6
Create Date: 2025-10-18 16:32:03.255077

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1aff281bc719'
down_revision = ('add_photo_comment', '20251013_profile_pic', 'f1a2b3c4d5e6')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
