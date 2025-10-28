"""
Database Migration
Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.
"""

"""Add enhancement metadata fields to Photo model

Revision ID: 20251012_105417
Revises: 20251012_082532
Create Date: 2025-10-12 10:54:17

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251012_105417'
down_revision = '20251012_082532'
branch_labels = None
depends_on = None


def upgrade():
    # Add edited_path column
    op.add_column('photo', sa.Column('edited_path', sa.String(500), nullable=True))
    
    # Add enhancement_metadata JSON column
    op.add_column('photo', sa.Column('enhancement_metadata', sa.JSON(), nullable=True))


def downgrade():
    # Remove enhancement_metadata column
    op.drop_column('photo', 'enhancement_metadata')
    
    # Remove edited_path column
    op.drop_column('photo', 'edited_path')
