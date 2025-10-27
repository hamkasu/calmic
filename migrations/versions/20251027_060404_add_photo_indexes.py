"""add photo indexes

Revision ID: 20251027_060404
Revises: e4254a8d276f
Create Date: 2025-10-27 06:04:04.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251027_060404'
down_revision = 'e4254a8d276f'
branch_labels = None
depends_on = None


def upgrade():
    # Add indexes to Photo table for optimized queries
    # These indexes will dramatically speed up gallery queries
    
    # Index on user_id for filtering photos by user
    op.create_index('ix_photo_user_id', 'photo', ['user_id'], unique=False)
    
    # Index on created_at for sorting by date
    op.create_index('ix_photo_created_at', 'photo', ['created_at'], unique=False)
    
    # Composite index on user_id + created_at for optimal gallery queries
    # This allows efficient filtering by user AND sorting by date in a single index scan
    op.create_index('ix_photo_user_created', 'photo', ['user_id', 'created_at'], unique=False)


def downgrade():
    # Remove indexes
    op.drop_index('ix_photo_user_created', table_name='photo')
    op.drop_index('ix_photo_created_at', table_name='photo')
    op.drop_index('ix_photo_user_id', table_name='photo')
