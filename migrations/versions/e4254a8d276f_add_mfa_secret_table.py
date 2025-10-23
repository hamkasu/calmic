"""add_mfa_secret_table

Revision ID: e4254a8d276f
Revises: 20251012_082532
Create Date: 2025-10-23 03:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = 'e4254a8d276f'
down_revision = '20251012_082532'
branch_labels = None
depends_on = None


def upgrade():
    # Create mfa_secret table if it doesn't exist
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    if 'mfa_secret' not in inspector.get_table_names():
        op.create_table('mfa_secret',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('secret', sa.String(length=32), nullable=False),
            sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('backup_codes', sa.Text(), nullable=True),
            sa.Column('enabled_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
            sa.Column('last_used_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id')
        )
        
        # Create index on user_id for faster lookups
        op.create_index('ix_mfa_secret_user_id', 'mfa_secret', ['user_id'], unique=True)
        
        print("✓ Created mfa_secret table successfully")
    else:
        print("✓ mfa_secret table already exists, skipping")


def downgrade():
    # Drop mfa_secret table if it exists
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    if 'mfa_secret' in inspector.get_table_names():
        op.drop_index('ix_mfa_secret_user_id', table_name='mfa_secret')
        op.drop_table('mfa_secret')
        print("✓ Dropped mfa_secret table successfully")
    else:
        print("✓ mfa_secret table doesn't exist, skipping")
