"""add conversations and web sources

Revision ID: week3_conversations
Revises: f898a8010080
Create Date: 2025-11-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

revision = 'week3_conversations'
down_revision = 'f898a8010080'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('title', sa.String(255)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()')),
    )
    op.create_index('idx_conversations_user', 'conversations', ['user_id'])
    op.create_index('idx_conversations_created', 'conversations', ['created_at'])

    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversations.id'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('meta_data', postgresql.JSONB(), server_default='{}'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()')),
    )
    op.create_index('idx_messages_conversation', 'messages', ['conversation_id'])

    op.create_table(
        'web_sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('url', sa.String(1000), nullable=False, unique=True),
        sa.Column('title', sa.String(500)),
        sa.Column('content', sa.Text()),
        sa.Column('embedding', Vector(512)),
        sa.Column('scraped_at', sa.DateTime(), server_default=sa.text('NOW()')),
        sa.Column('meta_data', postgresql.JSONB(), server_default='{}'),
    )
    op.create_index('idx_web_sources_url', 'web_sources', ['url'])
    
    op.execute("""
        CREATE INDEX idx_web_sources_embedding ON web_sources 
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)


def downgrade() -> None:
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('web_sources')
