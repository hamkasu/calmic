"""Add grid_thumbnail_path and blurhash columns to photo table

Revision ID: 20251030_add_grid_thumbnail_and_blurhash
Revises: 20251024_015608_ai_quotas
Create Date: 2025-10-30 04:00:00.000000

This migration adds the grid_thumbnail_path and blurhash columns to support
optimized gallery grid display with instant placeholder previews.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '20251030_add_grid_thumbnail_and_blurhash'
down_revision = '20251024_015608_ai_quotas'
branch_labels = None
depends_on = None


def column_exists(table_name, column_name):
    """Check if a column exists in the table"""
    try:
        conn = op.get_bind()
        inspector = inspect(conn)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return column_name in columns
    except Exception:
        return False


def upgrade():
    """Add grid_thumbnail_path and blurhash columns if they don't exist"""
    
    # Add grid_thumbnail_path column (Small 200x200 thumbnail for gallery grid)
    if not column_exists('photo', 'grid_thumbnail_path'):
        op.add_column('photo', sa.Column('grid_thumbnail_path', sa.String(500), nullable=True))
        print("✅ Added grid_thumbnail_path column to photo table")
    else:
        print("ℹ️  grid_thumbnail_path column already exists, skipping")
    
    # Add blurhash column (Blurhash for instant placeholder preview)
    if not column_exists('photo', 'blurhash'):
        op.add_column('photo', sa.Column('blurhash', sa.String(100), nullable=True))
        print("✅ Added blurhash column to photo table")
    else:
        print("ℹ️  blurhash column already exists, skipping")


def downgrade():
    """Remove grid_thumbnail_path and blurhash columns if they exist"""
    
    # Drop grid_thumbnail_path column
    if column_exists('photo', 'grid_thumbnail_path'):
        op.drop_column('photo', 'grid_thumbnail_path')
        print("✅ Removed grid_thumbnail_path column from photo table")
    else:
        print("ℹ️  grid_thumbnail_path column doesn't exist, skipping")
    
    # Drop blurhash column
    if column_exists('photo', 'blurhash'):
        op.drop_column('photo', 'blurhash')
        print("✅ Removed blurhash column from photo table")
    else:
        print("ℹ️  blurhash column doesn't exist, skipping")
