"""Add PhotoComment table for photo annotations

Revision ID: add_photo_comment
Revises: 
Create Date: 2025-10-12 08:26:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_photo_comment'
down_revision = 'ad11b5287a15'  # Points to add_last_sent_at migration
branch_labels = None
depends_on = None


def upgrade():
    # Create photo_comment table
    op.create_table('photo_comment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('photo_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('comment_text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['photo_id'], ['photo.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better performance
    op.create_index(op.f('ix_photo_comment_photo_id'), 'photo_comment', ['photo_id'], unique=False)
    op.create_index(op.f('ix_photo_comment_user_id'), 'photo_comment', ['user_id'], unique=False)


def downgrade():
    # Drop indexes
    op.drop_index(op.f('ix_photo_comment_user_id'), table_name='photo_comment')
    op.drop_index(op.f('ix_photo_comment_photo_id'), table_name='photo_comment')
    
    # Drop table
    op.drop_table('photo_comment')
