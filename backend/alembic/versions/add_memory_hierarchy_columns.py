"""Add missing columns to memories table for hierarchical memory

Revision ID: add_memory_hierarchy_columns
Revises: namespace_migration_001
Create Date: 2025-11-22

This migration adds memory_type, importance_score, and last_accessed columns
to support the hierarchical memory system.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision = 'add_memory_hierarchy_columns'
down_revision = 'namespace_migration_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add missing columns to memories table."""
    
    # Add memory_type column
    op.add_column('memories', sa.Column('memory_type', sa.String(50), nullable=False, server_default='episodic'))
    op.create_index('ix_memories_memory_type', 'memories', ['memory_type'])
    
    # Add importance_score column
    op.add_column('memories', sa.Column('importance_score', sa.Integer, nullable=False, server_default='50'))
    
    # Add last_accessed column
    op.add_column('memories', sa.Column('last_accessed', sa.DateTime, nullable=False, server_default=sa.func.now()))
    op.create_index('ix_memories_last_accessed', 'memories', ['last_accessed'])
    
    # Remove server defaults after initial population
    op.alter_column('memories', 'memory_type', server_default=None)
    op.alter_column('memories', 'importance_score', server_default=None)
    op.alter_column('memories', 'last_accessed', server_default=None)


def downgrade() -> None:
    """Remove the added columns."""
    op.drop_index('ix_memories_last_accessed', table_name='memories')
    op.drop_column('memories', 'last_accessed')
    op.drop_column('memories', 'importance_score')
    op.drop_index('ix_memories_memory_type', table_name='memories')
    op.drop_column('memories', 'memory_type')
