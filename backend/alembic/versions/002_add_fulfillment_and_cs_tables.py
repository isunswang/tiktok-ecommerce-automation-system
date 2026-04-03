"""Add fulfillment and customer service tables.

Revision ID: 002
Revises: 001
Create Date: 2025-01-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create forwarders table
    op.create_table(
        'forwarders',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('contact_name', sa.String(200), nullable=True),
        sa.Column('contact_phone', sa.String(50), nullable=True),
        sa.Column('contact_email', sa.String(200), nullable=True),
        sa.Column('province', sa.String(100), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('district', sa.String(100), nullable=True),
        sa.Column('address', sa.String(500), nullable=True),
        sa.Column('postal_code', sa.String(20), nullable=True),
        sa.Column('api_endpoint', sa.String(500), nullable=True),
        sa.Column('api_key', sa.String(500), nullable=True),
        sa.Column('api_secret', sa.String(500), nullable=True),
        sa.Column('supported_countries', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('remark', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_forwarders_code'), 'forwarders', ['code'], unique=False)
    op.create_index(op.f('ix_forwarders_status'), 'forwarders', ['status'], unique=False)

    # Create sku_mappings table
    op.create_table(
        'sku_mappings',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tiktok_product_id', sa.String(100), nullable=False),
        sa.Column('tiktok_sku_id', sa.String(100), nullable=False),
        sa.Column('tiktok_sku_name', sa.String(500), nullable=True),
        sa.Column('alibaba_product_id', sa.String(100), nullable=False),
        sa.Column('alibaba_sku_id', sa.String(100), nullable=True),
        sa.Column('alibaba_sku_name', sa.String(500), nullable=True),
        sa.Column('supplier_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('match_method', sa.String(50), nullable=False),
        sa.Column('confidence_score', sa.Float, nullable=True),
        sa.Column('spec_mapping', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('tiktok_price', sa.Numeric(12, 2), nullable=True),
        sa.Column('alibaba_price', sa.Numeric(12, 2), nullable=True),
        sa.Column('tiktok_image_url', sa.String(1000), nullable=True),
        sa.Column('alibaba_image_url', sa.String(1000), nullable=True),
        sa.Column('remark', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='SET NULL')
    )
    op.create_index(op.f('ix_sku_mappings_tiktok_product_id'), 'sku_mappings', ['tiktok_product_id'], unique=False)
    op.create_index(op.f('ix_sku_mappings_tiktok_sku_id'), 'sku_mappings', ['tiktok_sku_id'], unique=False)
    op.create_index(op.f('ix_sku_mappings_alibaba_product_id'), 'sku_mappings', ['alibaba_product_id'], unique=False)
    op.create_index(op.f('ix_sku_mappings_alibaba_sku_id'), 'sku_mappings', ['alibaba_sku_id'], unique=False)
    op.create_index(op.f('ix_sku_mappings_status'), 'sku_mappings', ['status'], unique=False)

    # Create match_records table
    op.create_table(
        'match_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sku_mapping_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('match_method', sa.String(50), nullable=False),
        sa.Column('confidence_score', sa.Float, nullable=True),
        sa.Column('is_matched', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('match_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('failure_reason', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['order_item_id'], ['order_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sku_mapping_id'], ['sku_mappings.id'], ondelete='SET NULL')
    )
    op.create_index(op.f('ix_match_records_order_id'), 'match_records', ['order_id'], unique=False)
    op.create_index(op.f('ix_match_records_order_item_id'), 'match_records', ['order_item_id'], unique=False)
    op.create_index(op.f('ix_match_records_sku_mapping_id'), 'match_records', ['sku_mapping_id'], unique=False)
    op.create_index(op.f('ix_match_records_is_matched'), 'match_records', ['is_matched'], unique=False)

    # Create alerts table
    op.create_table(
        'alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('alert_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False, server_default='medium'),
        sa.Column('status', sa.String(20), nullable=False, server_default='open'),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('related_order_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('related_purchase_order_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('related_supplier_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('alert_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('resolution_note', sa.Text, nullable=True),
        sa.Column('resolved_at', sa.String(50), nullable=True),
        sa.Column('notification_sent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('notification_channels', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['related_order_id'], ['orders.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['related_purchase_order_id'], ['purchase_orders.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['related_supplier_id'], ['suppliers.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['resolved_by'], ['users.id'], ondelete='SET NULL')
    )
    op.create_index(op.f('ix_alerts_alert_type'), 'alerts', ['alert_type'], unique=False)
    op.create_index(op.f('ix_alerts_severity'), 'alerts', ['severity'], unique=False)
    op.create_index(op.f('ix_alerts_status'), 'alerts', ['status'], unique=False)
    op.create_index(op.f('ix_alerts_related_order_id'), 'alerts', ['related_order_id'], unique=False)
    op.create_index(op.f('ix_alerts_related_purchase_order_id'), 'alerts', ['related_purchase_order_id'], unique=False)
    op.create_index(op.f('ix_alerts_related_supplier_id'), 'alerts', ['related_supplier_id'], unique=False)
    op.create_index(op.f('ix_alerts_assigned_to'), 'alerts', ['assigned_to'], unique=False)

    # Create faqs table
    op.create_table(
        'faqs',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('question', sa.String(1000), nullable=False),
        sa.Column('answer', sa.Text, nullable=False),
        sa.Column('question_en', sa.String(1000), nullable=True),
        sa.Column('answer_en', sa.Text, nullable=True),
        sa.Column('keywords', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('match_rules', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('view_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('helpful_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('applicable_sites', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_faqs_category'), 'faqs', ['category'], unique=False)
    op.create_index(op.f('ix_faqs_status'), 'faqs', ['status'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_faqs_status'), table_name='faqs')
    op.drop_index(op.f('ix_faqs_category'), table_name='faqs')
    op.drop_table('faqs')

    op.drop_index(op.f('ix_alerts_assigned_to'), table_name='alerts')
    op.drop_index(op.f('ix_alerts_related_supplier_id'), table_name='alerts')
    op.drop_index(op.f('ix_alerts_related_purchase_order_id'), table_name='alerts')
    op.drop_index(op.f('ix_alerts_related_order_id'), table_name='alerts')
    op.drop_index(op.f('ix_alerts_status'), table_name='alerts')
    op.drop_index(op.f('ix_alerts_severity'), table_name='alerts')
    op.drop_index(op.f('ix_alerts_alert_type'), table_name='alerts')
    op.drop_table('alerts')

    op.drop_index(op.f('ix_match_records_is_matched'), table_name='match_records')
    op.drop_index(op.f('ix_match_records_sku_mapping_id'), table_name='match_records')
    op.drop_index(op.f('ix_match_records_order_item_id'), table_name='match_records')
    op.drop_index(op.f('ix_match_records_order_id'), table_name='match_records')
    op.drop_table('match_records')

    op.drop_index(op.f('ix_sku_mappings_status'), table_name='sku_mappings')
    op.drop_index(op.f('ix_sku_mappings_alibaba_sku_id'), table_name='sku_mappings')
    op.drop_index(op.f('ix_sku_mappings_alibaba_product_id'), table_name='sku_mappings')
    op.drop_index(op.f('ix_sku_mappings_tiktok_sku_id'), table_name='sku_mappings')
    op.drop_index(op.f('ix_sku_mappings_tiktok_product_id'), table_name='sku_mappings')
    op.drop_table('sku_mappings')

    op.drop_index(op.f('ix_forwarders_status'), table_name='forwarders')
    op.drop_index(op.f('ix_forwarders_code'), table_name='forwarders')
    op.drop_table('forwarders')
