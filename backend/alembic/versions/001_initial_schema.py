"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2026-09-28 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. users table (this usually syncs with Supabase auth.users, but we keep a local reference)
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('email', sa.String(), nullable=False, unique=True),
        sa.Column('role', sa.String(), nullable=False, server_default='citizen'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )

    # 2. user_profiles
    op.create_table(
        'user_profiles',
        sa.Column('id', sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', sa.UUID(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('gender', sa.String(), nullable=True),
        sa.Column('state', sa.String(), nullable=True),
        sa.Column('district', sa.String(), nullable=True),
        sa.Column('occupation', sa.String(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('annual_income', sa.Numeric(), nullable=True),
        sa.Column('land_holding_acres', sa.Numeric(), nullable=True),
        sa.Column('is_bpl', sa.Boolean(), nullable=True),
        sa.Column('is_disabled', sa.Boolean(), nullable=True),
        sa.Column('additional_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )

    # 3. schemes
    op.create_table(
        'schemes',
        sa.Column('id', sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('slug', sa.String(), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('ministry', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('target_states', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('benefits_summary', sa.Text(), nullable=False),
        sa.Column('eligibility_summary', sa.Text(), nullable=False),
        sa.Column('application_url', sa.String(), nullable=True),
        sa.Column('deadline', sa.Date(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )

    # 4. scheme_rules
    op.create_table(
        'scheme_rules',
        sa.Column('id', sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column('scheme_id', sa.UUID(), sa.ForeignKey('schemes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rule_definition', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('version', sa.Integer(), server_default='1'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )

    # 5. eligibility_checks
    op.create_table(
        'eligibility_checks',
        sa.Column('id', sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', sa.UUID(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('submitted_profile', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('matched_count', sa.Integer(), server_default='0'),
        sa.Column('checked_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )

    # 6. eligibility_results
    op.create_table(
        'eligibility_results',
        sa.Column('id', sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column('check_id', sa.UUID(), sa.ForeignKey('eligibility_checks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('scheme_id', sa.UUID(), sa.ForeignKey('schemes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('match_percentage', sa.Numeric(), nullable=False),
        sa.Column('matched_rules', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('failed_rules', postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )

    # 7. documents
    op.create_table(
        'documents',
        sa.Column('id', sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', sa.UUID(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('file_name', sa.String(), nullable=False),
        sa.Column('file_type', sa.String(), nullable=False),
        sa.Column('storage_path', sa.String(), nullable=False),
        sa.Column('document_category', sa.String(), nullable=True),
        sa.Column('status', sa.String(), server_default='uploaded'),
        sa.Column('file_size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )

    # 8. ocr_results
    op.create_table(
        'ocr_results',
        sa.Column('id', sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column('document_id', sa.UUID(), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('raw_text', sa.Text(), nullable=False),
        sa.Column('extracted_fields', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('confidence_score', sa.Numeric(), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )

    # 9. checklists
    op.create_table(
        'checklists',
        sa.Column('id', sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', sa.UUID(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('scheme_id', sa.UUID(), sa.ForeignKey('schemes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(), server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )

    # 10. checklist_items
    op.create_table(
        'checklist_items',
        sa.Column('id', sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column('checklist_id', sa.UUID(), sa.ForeignKey('checklists.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_completed', sa.Boolean(), server_default='false'),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True)
    )
    
    # 11. notifications
    op.create_table(
        'notifications',
        sa.Column('id', sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', sa.UUID(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_read', sa.Boolean(), server_default='false'),
        sa.Column('sent_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )


def downgrade() -> None:
    op.drop_table('notifications')
    op.drop_table('checklist_items')
    op.drop_table('checklists')
    op.drop_table('ocr_results')
    op.drop_table('documents')
    op.drop_table('eligibility_results')
    op.drop_table('eligibility_checks')
    op.drop_table('scheme_rules')
    op.drop_table('schemes')
    op.drop_table('user_profiles')
    op.drop_table('users')
