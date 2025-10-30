"""Add AI enhancement quotas and update subscription plans

Revision ID: 20251024_015608_ai_quotas
Revises: e4254a8d276f
Create Date: 2025-10-24 01:56:08.000000

"""
from alembic import op
import sqlalchemy as sa
from decimal import Decimal

# revision identifiers, used by Alembic.
revision = '20251024_015608_ai_quotas'
down_revision = 'e4254a8d276f'
branch_labels = None
depends_on = None

def upgrade():
    # Change storage_gb to NUMERIC to support decimal values
    op.alter_column('subscription_plan', 'storage_gb',
               existing_type=sa.INTEGER(),
               type_=sa.Numeric(precision=10, scale=2),
               existing_nullable=False)
    
    # Add AI enhancement quota to subscription plans
    op.add_column('subscription_plan', sa.Column('ai_enhancement_quota', sa.Integer(), nullable=False, server_default='0'))
    
    # Add AI enhancement tracking to user subscriptions
    op.add_column('user_subscription', sa.Column('ai_enhancements_used', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('user_subscription', sa.Column('ai_enhancements_reset_date', sa.DateTime(), nullable=True))
    
    # Deactivate old plans
    op.execute("UPDATE subscription_plan SET is_active = false WHERE name IN ('basic', 'standard', 'premium')")

def downgrade():
    op.drop_column('user_subscription', 'ai_enhancements_reset_date')
    op.drop_column('user_subscription', 'ai_enhancements_used')
    op.drop_column('subscription_plan', 'ai_enhancement_quota')
    
    op.alter_column('subscription_plan', 'storage_gb',
               existing_type=sa.Numeric(precision=10, scale=2),
               type_=sa.INTEGER(),
               existing_nullable=False)
    
    # Reactivate old plans
    op.execute("UPDATE subscription_plan SET is_active = true WHERE name IN ('basic', 'standard', 'premium')")
