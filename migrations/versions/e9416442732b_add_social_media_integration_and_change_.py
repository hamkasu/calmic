"""add_social_media_integration_and_change_storage_gb_to_numeric

Revision ID: e9416442732b
Revises: ad11b5287a15
Create Date: 2025-10-03 04:11:17.502820

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e9416442732b'
down_revision = 'ad11b5287a15'
branch_labels = None
depends_on = None


def upgrade():
    # Add social_media_integration column and change storage_gb to NUMERIC
    # Use direct PostgreSQL-compatible commands instead of batch_alter_table
    
    # Add social_media_integration column if it doesn't exist
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('subscription_plan')]
    
    if 'social_media_integration' not in columns:
        op.add_column('subscription_plan', sa.Column('social_media_integration', sa.BOOLEAN(), server_default=sa.text('false'), nullable=True))
    
    # Change storage_gb type to NUMERIC for PostgreSQL
    # This allows decimal storage sizes like 0.1 GB
    if 'storage_gb' in columns:
        op.alter_column('subscription_plan', 'storage_gb',
                       existing_type=sa.Integer(),
                       type_=sa.NUMERIC(precision=10, scale=2),
                       existing_nullable=False,
                       postgresql_using='storage_gb::numeric')


def downgrade():
    # Remove social_media_integration column and change storage_gb back to Integer
    # Use direct PostgreSQL-compatible commands
    
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('subscription_plan')]
    
    if 'storage_gb' in columns:
        op.alter_column('subscription_plan', 'storage_gb',
                       existing_type=sa.NUMERIC(precision=10, scale=2),
                       type_=sa.Integer(),
                       existing_nullable=False,
                       postgresql_using='storage_gb::integer')
    
    if 'social_media_integration' in columns:
        op.drop_column('subscription_plan', 'social_media_integration')
