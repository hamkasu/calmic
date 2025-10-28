"""add_enhanced_photo_tracking_columns

Revision ID: g2a3b4c5d6e7
Revises: f1a2b3c4d5e6
Create Date: 2025-10-28 03:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'g2a3b4c5d6e7'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    # Add original_photo_id column to track the original photo for enhanced versions
    with op.batch_alter_table('photo', schema=None) as batch_op:
        batch_op.add_column(sa.Column('original_photo_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('is_enhanced_version', sa.Boolean(), nullable=False, server_default='false'))
        batch_op.add_column(sa.Column('enhancement_type', sa.String(length=50), nullable=True))
        batch_op.create_foreign_key('fk_photo_original_photo_id', 'photo', ['original_photo_id'], ['id'])


def downgrade():
    # Remove the enhanced photo tracking columns
    with op.batch_alter_table('photo', schema=None) as batch_op:
        batch_op.drop_constraint('fk_photo_original_photo_id', type_='foreignkey')
        batch_op.drop_column('enhancement_type')
        batch_op.drop_column('is_enhanced_version')
        batch_op.drop_column('original_photo_id')
