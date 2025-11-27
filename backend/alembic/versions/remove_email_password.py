"""Remove email and password_hash columns from users table

Revision ID: remove_email_password_001
Revises: add_memory_hierarchy_columns
Create Date: 2025-11-22

This migration removes email and password_hash columns as namespace is now the sole identifier.
"""
from alembic import op
import sqlalchemy as sa

revision = 'remove_email_password_001'
down_revision = 'add_memory_hierarchy_columns'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Remove email and password_hash columns."""
    # Drop email column
    op.drop_column('users', 'email')
    
    # Drop password_hash column
    op.drop_column('users', 'password_hash')


def downgrade() -> None:
    """Add back email and password_hash columns."""
    # Add back password_hash column
    op.add_column('users', sa.Column('password_hash', sa.String(255), nullable=True))
    
    # Add back email column
    op.add_column('users', sa.Column('email', sa.String(255), nullable=False))
    op.create_unique_constraint('users_email_key', 'users', ['email'])
