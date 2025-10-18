"""add profile_picture to user table

Revision ID: 20251013_profile_pic
Revises: ad11b5287a15
Create Date: 2025-10-13 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251013_profile_pic'
down_revision = 'ad11b5287a15'
branch_labels = None
depends_on = None


def upgrade():
    # Add profile_picture column to user table
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('profile_picture', sa.String(length=500), nullable=True))


def downgrade():
    # Remove profile_picture column from user table
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('profile_picture')
