"""
Alembic migration: Add tables for hierarchical memory management
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from pgvector.sqlalchemy import Vector
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'memory_hierarchy'
down_revision = 'week4_user_preferences'
branch_labels = None
depends_on = None


def upgrade():
    # Create MemoryAccess table for tracking memory usage
    op.create_table(
        'memory_access',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('memory_id', UUID(as_uuid=True), sa.ForeignKey('memories.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('access_type', sa.String(50), nullable=False),  # 'retrieval', 'edit', 'view'
        sa.Column('accessed_at', sa.DateTime, nullable=False, default=datetime.utcnow, index=True),
        sa.Column('metadata', JSONB, default={})
    )
    
    # Create MemorySummary table for consolidated semantic memories
    op.create_table(
        'memory_summaries',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('summary_text', sa.Text, nullable=False),
        sa.Column('summary_embedding', Vector(512), nullable=False),
        sa.Column('source_memory_ids', ARRAY(sa.String), nullable=False),  # Array of memory UUIDs
        sa.Column('memory_count', sa.Integer, nullable=False),
        sa.Column('date_range_start', sa.DateTime, nullable=False),
        sa.Column('date_range_end', sa.DateTime, nullable=False),
        sa.Column('importance_score', sa.Float, default=0.0),
        sa.Column('created_at', sa.DateTime, nullable=False, default=datetime.utcnow, index=True),
        sa.Column('updated_at', sa.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    )
    
    # Add memory_type column to existing memories table
    op.add_column('memories', sa.Column('memory_type', sa.String(50), default='episodic', index=True))
    
    # Add importance_score column to memories table
    op.add_column('memories', sa.Column('importance_score', sa.Float, default=0.5))
    
    # Add last_accessed column to memories table
    op.add_column('memories', sa.Column('last_accessed', sa.DateTime, default=datetime.utcnow, index=True))
    
    # Create indexes for better query performance
    op.create_index('idx_memory_access_accessed_at', 'memory_access', ['accessed_at'])
    op.create_index('idx_memory_summaries_date_range', 'memory_summaries', ['date_range_start', 'date_range_end'])
    op.create_index('idx_memory_summaries_importance', 'memory_summaries', ['importance_score'])
    op.create_index('idx_memories_type_created', 'memories', ['memory_type', 'created_at'])
    op.create_index('idx_memories_importance', 'memories', ['importance_score'])
    
    # Create vector index for memory summaries
    op.execute("""
        CREATE INDEX idx_memory_summaries_embedding ON memory_summaries 
        USING ivfflat (summary_embedding vector_cosine_ops)
        WITH (lists = 100);
    """)


def downgrade():
    # Drop indexes
    op.drop_index('idx_memory_access_accessed_at', 'memory_access')
    op.drop_index('idx_memory_summaries_date_range', 'memory_summaries')
    op.drop_index('idx_memory_summaries_importance', 'memory_summaries')
    op.drop_index('idx_memories_type_created', 'memories')
    op.drop_index('idx_memories_importance', 'memories')
    op.execute("DROP INDEX IF EXISTS idx_memory_summaries_embedding")
    
    # Drop columns from memories
    op.drop_column('memories', 'memory_type')
    op.drop_column('memories', 'importance_score')
    op.drop_column('memories', 'last_accessed')
    
    # Drop tables
    op.drop_table('memory_summaries')
    op.drop_table('memory_access')
