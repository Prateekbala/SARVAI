"""Add OCR, Layout, BM25, and Re-ranking support to memories and embeddings

Revision ID: add_ocr_layout_reranking
Revises: user_preferences
Create Date: 2025-11-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_ocr_layout_reranking'
down_revision = 'user_preferences'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add OCR and layout columns to memories table
    op.add_column('memories', sa.Column('ocr_text', sa.Text(), nullable=True))
    op.add_column('memories', sa.Column('layout_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    
    # Add re-ranking and BM25 columns to embeddings table
    op.add_column('embeddings', sa.Column('bm25_score', sa.Integer(), default=0, nullable=True))
    op.add_column('embeddings', sa.Column('re_ranking_score', sa.Integer(), default=0, nullable=True))


def downgrade() -> None:
    # Remove columns in reverse order
    op.drop_column('embeddings', 're_ranking_score')
    op.drop_column('embeddings', 'bm25_score')
    op.drop_column('memories', 'layout_data')
    op.drop_column('memories', 'ocr_text')
