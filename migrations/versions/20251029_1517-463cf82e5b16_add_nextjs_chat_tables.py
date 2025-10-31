"""add_nextjs_chat_tables

Revision ID: 463cf82e5b16
Revises: f3c222debe2a
Create Date: 2025-10-29 15:17:59.531893

Adds Next.js chat application tables to the unified database:
- Extends users table with password field for Next.js auth compatibility
- Chat: AI chat sessions
- Message_v2: Chat messages with parts and attachments
- Vote_v2: Message voting system
- Document: AI-generated documents (text, code, image, sheet, crud)
- Suggestion: Document editing suggestions
- Stream: Streaming session tracking
- Feedback: User feedback system

This migration unifies the previously separate Neon database with the local PostgreSQL.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '463cf82e5b16'
down_revision = 'f3c222debe2a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============================================
    # 1. EXTEND USERS TABLE FOR NEXT.JS AUTH
    # ============================================
    # Add password field to users table (nullable for existing users and OAuth users)
    op.add_column('users', sa.Column('password', sa.String(length=64), nullable=True))

    # ============================================
    # 2. CHAT TABLE
    # ============================================
    op.create_table('chat',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('visibility', sa.String(length=7), nullable=False, server_default='private'),
        sa.Column('last_context', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='AI chat sessions'
    )
    op.create_index('ix_chat_user_id', 'chat', ['user_id'])
    op.create_index('ix_chat_created_at', 'chat', ['created_at'])

    # ============================================
    # 3. MESSAGE_V2 TABLE
    # ============================================
    op.create_table('message_v2',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('chat_id', sa.Uuid(), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('parts', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('attachments', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['chat_id'], ['chat.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Chat messages with structured parts and attachments'
    )
    op.create_index('ix_message_v2_chat_id', 'message_v2', ['chat_id'])
    op.create_index('ix_message_v2_created_at', 'message_v2', ['created_at'])

    # ============================================
    # 4. VOTE_V2 TABLE
    # ============================================
    op.create_table('vote_v2',
        sa.Column('chat_id', sa.Uuid(), nullable=False),
        sa.Column('message_id', sa.Uuid(), nullable=False),
        sa.Column('is_upvoted', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['chat_id'], ['chat.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['message_id'], ['message_v2.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('chat_id', 'message_id'),
        comment='Message voting system'
    )

    # ============================================
    # 5. DOCUMENT TABLE
    # ============================================
    op.create_table('document',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('kind', sa.String(length=10), nullable=False, server_default='text'),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', 'created_at'),
        comment='AI-generated documents (text, code, image, sheet, crud)'
    )
    op.create_index('ix_document_user_id', 'document', ['user_id'])
    op.create_index('ix_document_created_at', 'document', ['created_at'])

    # ============================================
    # 6. SUGGESTION TABLE
    # ============================================
    op.create_table('suggestion',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('document_id', sa.Uuid(), nullable=False),
        sa.Column('document_created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('original_text', sa.Text(), nullable=False),
        sa.Column('suggested_text', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_resolved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['document_id', 'document_created_at'], ['document.id', 'document.created_at'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Document editing suggestions'
    )
    op.create_index('ix_suggestion_document_id', 'suggestion', ['document_id'])
    op.create_index('ix_suggestion_user_id', 'suggestion', ['user_id'])

    # ============================================
    # 7. STREAM TABLE
    # ============================================
    op.create_table('stream',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('chat_id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['chat_id'], ['chat.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Streaming session tracking'
    )
    op.create_index('ix_stream_chat_id', 'stream', ['chat_id'])

    # ============================================
    # 8. FEEDBACK TABLE
    # ============================================
    op.create_table('feedback',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=20), nullable=False, server_default='feature'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='under-review'),
        sa.Column('upvotes', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='User feedback system'
    )
    op.create_index('ix_feedback_user_id', 'feedback', ['user_id'])
    op.create_index('ix_feedback_category', 'feedback', ['category'])
    op.create_index('ix_feedback_status', 'feedback', ['status'])


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign key constraints)
    op.drop_table('feedback')
    op.drop_table('stream')
    op.drop_table('suggestion')
    op.drop_table('document')
    op.drop_table('vote_v2')
    op.drop_table('message_v2')
    op.drop_table('chat')

    # Remove password column from users
    op.drop_column('users', 'password')
