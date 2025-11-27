"""Migrate user identification from UUID to namespace

Revision ID: namespace_migration_001
Revises: week4_user_preferences
Create Date: 2025-01-15

This migration converts users table from UUID-based to namespace (String) based identification.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision = 'namespace_migration_001'
down_revision = 'week4_user_preferences'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade to namespace-based user identification."""
    
    # Step 1: Add namespace column to users and populate with email
    op.add_column('users', sa.Column('namespace', sa.String(255)))
    op.execute(text("UPDATE users SET namespace = email"))
    op.create_index('idx_users_namespace_unique', 'users', ['namespace'], unique=True)
    
    # Step 2-6: Process user_preferences table
    op.execute(text("ALTER TABLE user_preferences DROP CONSTRAINT IF EXISTS user_preferences_user_id_fkey CASCADE"))
    op.add_column('user_preferences', sa.Column('namespace', sa.String(255)))
    op.execute(text("""
        UPDATE user_preferences up
        SET namespace = u.namespace
        FROM users u
        WHERE up.user_id = u.id
    """))
    op.alter_column('user_preferences', 'namespace', nullable=False)
    op.drop_index('ix_user_preferences_user_id', table_name='user_preferences')
    op.drop_column('user_preferences', 'user_id')
    
    # Step 7: Process memories table
    op.execute(text("ALTER TABLE memories DROP CONSTRAINT IF EXISTS memories_user_id_fkey CASCADE"))
    op.add_column('memories', sa.Column('namespace', sa.String(255)))
    op.execute(text("""
        UPDATE memories m
        SET namespace = u.namespace
        FROM users u
        WHERE m.user_id = u.id
    """))
    op.alter_column('memories', 'namespace', nullable=False)
    op.drop_column('memories', 'user_id')
    
    # Step 8: Process conversations table
    op.execute(text("ALTER TABLE conversations DROP CONSTRAINT IF EXISTS conversations_user_id_fkey CASCADE"))
    op.add_column('conversations', sa.Column('namespace', sa.String(255)))
    op.execute(text("""
        UPDATE conversations c
        SET namespace = u.namespace
        FROM users u
        WHERE c.user_id = u.id
    """))
    op.alter_column('conversations', 'namespace', nullable=False)
    op.drop_column('conversations', 'user_id')
    
    # Step 9: Make namespace NOT NULL in users
    op.alter_column('users', 'namespace', nullable=False)
    
    # Step 10: Drop email unique constraint and drop id (primary key)
    op.execute(text("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_email_key"))
    op.drop_constraint('users_pkey', 'users', type_='primary')
    op.drop_column('users', 'id')
    
    # Step 11: Set namespace as primary key
    op.create_primary_key('users_pkey', 'users', ['namespace'])
    
    # Step 12: Create foreign keys for namespace
    op.create_foreign_key(
        'user_preferences_namespace_fkey',
        'user_preferences', 'users',
        ['namespace'], ['namespace'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'memories_namespace_fkey',
        'memories', 'users',
        ['namespace'], ['namespace'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'conversations_namespace_fkey',
        'conversations', 'users',
        ['namespace'], ['namespace'],
        ondelete='CASCADE'
    )
    
    # Step 13: Create indexes for namespace
    op.create_index('ix_user_preferences_namespace', 'user_preferences', ['namespace'])
    op.create_index('ix_memories_namespace', 'memories', ['namespace'])
    op.create_index('ix_conversations_namespace', 'conversations', ['namespace'])


def downgrade() -> None:
    """Downgrade is not supported for this migration."""
    raise NotImplementedError(
        "Downgrading from namespace migration is not supported. "
        "This is a data structure change that cannot be safely reversed."
    )
