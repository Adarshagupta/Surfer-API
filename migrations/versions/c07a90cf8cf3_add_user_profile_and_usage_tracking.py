"""add_user_profile_and_usage_tracking

Revision ID: c07a90cf8cf3
Revises: cd9536788099
Create Date: 2025-03-10 11:53:55.425609

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c07a90cf8cf3'
down_revision = 'cd9536788099'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to users table
    with op.batch_alter_table('users') as batch_op:
        # Profile information
        batch_op.add_column(sa.Column('avatar_url', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('bio', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('company', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('website', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('location', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('phone', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('preferences', sa.JSON(), nullable=True))
        
        # Account status
        batch_op.add_column(sa.Column('is_verified', sa.Boolean(), server_default='false', nullable=False))
        batch_op.add_column(sa.Column('email_verified', sa.Boolean(), server_default='false', nullable=False))
        
        # Usage and billing
        batch_op.add_column(sa.Column('api_quota', sa.Integer(), server_default='1000', nullable=False))
        batch_op.add_column(sa.Column('tokens_used', sa.Integer(), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('total_cost', sa.Numeric(10, 2), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('billing_status', sa.String(), server_default='free', nullable=False))
        batch_op.add_column(sa.Column('subscription_expires', sa.DateTime(timezone=True), nullable=True))
        
        # Additional timestamps
        batch_op.add_column(sa.Column('last_login', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('last_active', sa.DateTime(timezone=True), nullable=True))
    
    # Add new columns to usage_records table
    with op.batch_alter_table('usage_records') as batch_op:
        batch_op.add_column(sa.Column('cost', sa.Numeric(10, 4), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('response_time', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('error_message', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('request_metadata', sa.JSON(), nullable=True))


def downgrade():
    # Remove columns from users table
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('avatar_url')
        batch_op.drop_column('bio')
        batch_op.drop_column('company')
        batch_op.drop_column('website')
        batch_op.drop_column('location')
        batch_op.drop_column('phone')
        batch_op.drop_column('preferences')
        batch_op.drop_column('is_verified')
        batch_op.drop_column('email_verified')
        batch_op.drop_column('api_quota')
        batch_op.drop_column('tokens_used')
        batch_op.drop_column('total_cost')
        batch_op.drop_column('billing_status')
        batch_op.drop_column('subscription_expires')
        batch_op.drop_column('last_login')
        batch_op.drop_column('last_active')
    
    # Remove columns from usage_records table
    with op.batch_alter_table('usage_records') as batch_op:
        batch_op.drop_column('cost')
        batch_op.drop_column('response_time')
        batch_op.drop_column('error_message')
        batch_op.drop_column('request_metadata') 