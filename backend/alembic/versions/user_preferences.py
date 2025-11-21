"""Add user preferences and password

Revision ID: week4_user_preferences
Revises: add_conversations_and_web_sources
Create Date: 2025-11-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'week4_user_preferences'
down_revision = 'week3_conversations'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('users', sa.Column('password_hash', sa.String(length=255), nullable=True))
    
    op.create_table(
        'user_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('boost_topics', postgresql.ARRAY(sa.String()), server_default='{}'),
        sa.Column('suppress_topics', postgresql.ARRAY(sa.String()), server_default='{}'),
        sa.Column('search_preferences', postgresql.JSONB(), server_default='{}'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('ix_user_preferences_user_id', 'user_preferences', ['user_id'], unique=True)

def downgrade() -> None:
    op.drop_index('ix_user_preferences_user_id', table_name='user_preferences')
    op.drop_table('user_preferences')
    op.drop_column('users', 'password_hash')
