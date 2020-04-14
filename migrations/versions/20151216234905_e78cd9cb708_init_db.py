"""empty message

Revision ID: 5a4b01f8c986
Revises: 
Create Date: 2015-12-16 23:49:05.881388

"""

# revision identifiers, used by Alembic.
import sqlalchemy as sa
from alembic import op
from application.models.appmeta import AppMeta

revision = 'e78cd9cb708'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # start create tables
    op.create_table('app',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('created_on', sa.DateTime(), nullable=True),
                    sa.Column('updated_on', sa.DateTime(), nullable=True),
                    sa.Column('created_by', sa.String(length=50), nullable=True),
                    sa.Column('updated_by', sa.String(length=50), nullable=True),
                    sa.Column('name', sa.String(length=100), nullable=True),
                    sa.Column('type', sa.String(length=100), nullable=True),
                    sa.Column('desc', sa.String(length=200), nullable=True),
                    sa.Column('api_key', sa.String(length=100), nullable=True),
                    sa.Column('secret_key', sa.String(length=100), nullable=True),
                    sa.Column('version', sa.String(length=50), nullable=True),
                    sa.Column('version_num', sa.Integer(), nullable=True),
                    sa.Column('release_note', sa.String(length=2000), nullable=True),
                    sa.Column('download_url', sa.String(length=500), nullable=True),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('api_key'),
                    sa.UniqueConstraint('name')
                    )
    op.create_table('campaign',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('created_on', sa.DateTime(), nullable=True),
                    sa.Column('updated_on', sa.DateTime(), nullable=True),
                    sa.Column('created_by', sa.String(length=50), nullable=True),
                    sa.Column('updated_by', sa.String(length=50), nullable=True),
                    sa.Column('store_id', sa.BigInteger(), nullable=False),
                    sa.Column('title', sa.String(length=200), nullable=False),
                    sa.Column('content', sa.Text(), nullable=True),
                    sa.Column('related_cars', sa.String(length=200), nullable=True),
                    sa.Column('start', sa.Date(), nullable=False),
                    sa.Column('end', sa.Date(), nullable=False),
                    sa.Column('notify_date', sa.Date(), nullable=False),
                    sa.Column('notify_sent', sa.Boolean(), nullable=True),
                    sa.Column('source', sa.String(length=20), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_campaign_store_id'), 'campaign', ['store_id'], unique=False)
    op.create_table('frt_inventory',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('created_on', sa.DateTime(), nullable=True),
                    sa.Column('updated_on', sa.DateTime(), nullable=True),
                    sa.Column('created_by', sa.String(length=50), nullable=True),
                    sa.Column('updated_by', sa.String(length=50), nullable=True),
                    sa.Column('store_id', sa.BigInteger(), nullable=False),
                    sa.Column('brand_code', sa.String(length=100), nullable=True),
                    sa.Column('brand_name', sa.String(length=200), nullable=True),
                    sa.Column('class_code', sa.String(length=100), nullable=True),
                    sa.Column('class_name', sa.String(length=200), nullable=True),
                    sa.Column('cartype_code', sa.String(length=100), nullable=True),
                    sa.Column('cartype', sa.String(length=200), nullable=True),
                    sa.Column('subtype_code', sa.String(length=100), nullable=True),
                    sa.Column('subtype_name', sa.String(length=200), nullable=True),
                    sa.Column('color_name', sa.String(length=50), nullable=True),
                    sa.Column('color_attribute', sa.String(length=50), nullable=True),
                    sa.Column('warehouse_name', sa.String(length=200), nullable=True),
                    sa.Column('location_name', sa.String(length=200), nullable=True),
                    sa.Column('out_factory_date', sa.Date(), nullable=True),
                    sa.Column('vin', sa.String(length=50), nullable=True),
                    sa.Column('inv_status', sa.String(length=50), nullable=True),
                    sa.Column('invday', sa.Integer(), nullable=True),
                    sa.Column('in_price', sa.Numeric(precision=12, scale=2), nullable=True),
                    sa.Column('mrsp', sa.Numeric(precision=12, scale=2), nullable=True),
                    sa.Column('rebate_amt', sa.Numeric(precision=12, scale=2), nullable=True),
                    sa.Column('sync_timestamp', sa.Integer(), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_frt_inventory_store_id'), 'frt_inventory', ['store_id'], unique=False)
    op.create_table('frt_shared_inventory',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('created_on', sa.DateTime(), nullable=True),
                    sa.Column('updated_on', sa.DateTime(), nullable=True),
                    sa.Column('created_by', sa.String(length=50), nullable=True),
                    sa.Column('updated_by', sa.String(length=50), nullable=True),
                    sa.Column('store_id', sa.BigInteger(), nullable=False),
                    sa.Column('brand_code', sa.String(length=100), nullable=True),
                    sa.Column('brand_name', sa.String(length=200), nullable=True),
                    sa.Column('class_code', sa.String(length=100), nullable=True),
                    sa.Column('class_name', sa.String(length=200), nullable=True),
                    sa.Column('cartype_code', sa.String(length=100), nullable=True),
                    sa.Column('cartype', sa.String(length=200), nullable=True),
                    sa.Column('subtype_code', sa.String(length=100), nullable=True),
                    sa.Column('subtype_name', sa.String(length=200), nullable=True),
                    sa.Column('qty', sa.Integer(), nullable=True),
                    sa.Column('sync_timestamp', sa.Integer(), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_frt_shared_inventory_store_id'), 'frt_shared_inventory', ['store_id'], unique=False)
    op.create_table('hwjd_customer',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('created_on', sa.DateTime(), nullable=True),
                    sa.Column('updated_on', sa.DateTime(), nullable=True),
                    sa.Column('created_by', sa.String(length=50), nullable=True),
                    sa.Column('updated_by', sa.String(length=50), nullable=True),
                    sa.Column('reception_id', sa.BigInteger(), nullable=False),
                    sa.Column('customer_id', sa.BigInteger(), nullable=False),
                    sa.Column('store_id', sa.BigInteger(), nullable=False),
                    sa.Column('uuid', sa.String(length=50), nullable=True),
                    sa.Column('company_code', sa.String(length=50), nullable=False),
                    sa.Column('created_date', sa.Date(), nullable=True),
                    sa.Column('intent_car_code', sa.String(length=100), nullable=True),
                    sa.Column('intent_car_model', sa.String(length=100), nullable=True),
                    sa.Column('visit_type', sa.String(length=50), nullable=True),
                    sa.Column('rx_start', sa.String(length=100), nullable=True),
                    sa.Column('rx_end', sa.String(length=100), nullable=True),
                    sa.Column('rx_duration', sa.String(length=100), nullable=True),
                    sa.Column('rx_type', sa.String(length=50), nullable=True),
                    sa.Column('channel', sa.String(length=50), nullable=True),
                    sa.Column('sales', sa.String(length=50), nullable=True),
                    sa.Column('intent_car_name', sa.String(length=100), nullable=True),
                    sa.Column('intent_car_color', sa.String(length=50), nullable=True),
                    sa.Column('intent_order_date', sa.Date(), nullable=True),
                    sa.Column('budget', sa.String(length=50), nullable=True),
                    sa.Column('payment', sa.String(length=50), nullable=True),
                    sa.Column('purpose', sa.String(length=50), nullable=True),
                    sa.Column('purchase_type', sa.String(length=50), nullable=True),
                    sa.Column('intent_level', sa.String(length=50), nullable=True),
                    sa.Column('on_file', sa.String(length=50), nullable=True),
                    sa.Column('has_trail', sa.String(length=50), nullable=True),
                    sa.Column('name', sa.String(length=200), nullable=True),
                    sa.Column('age_group', sa.String(length=50), nullable=True),
                    sa.Column('gender', sa.String(length=50), nullable=True),
                    sa.Column('industry', sa.String(length=50), nullable=True),
                    sa.Column('district', sa.String(length=100), nullable=True),
                    sa.Column('mobile', sa.String(length=200), nullable=True),
                    sa.Column('has_order', sa.String(length=50), nullable=True),
                    sa.Column('dealership', sa.String(length=50), nullable=True),
                    sa.Column('discount', sa.String(length=50), nullable=True),
                    sa.Column('price', sa.String(length=50), nullable=True),
                    sa.Column('gadgets_gift', sa.String(length=50), nullable=True),
                    sa.Column('gadgets_purchase', sa.String(length=50), nullable=True),
                    sa.Column('competing_car_brand', sa.String(length=100), nullable=True),
                    sa.Column('competing_car_name', sa.String(length=100), nullable=True),
                    sa.Column('used_car_model', sa.String(length=100), nullable=True),
                    sa.Column('used_car_value', sa.String(length=50), nullable=True),
                    sa.Column('has_used_car_assessed', sa.String(length=50), nullable=True),
                    sa.Column('remark', sa.String(length=500), nullable=True),
                    sa.Column('last_sync_date', sa.DateTime(), nullable=True),
                    sa.Column('last_sync_status', sa.Integer(), nullable=True),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('reception_id'),
                    sa.UniqueConstraint('uuid')
                    )
    op.create_index(op.f('ix_hwjd_customer_store_id'), 'hwjd_customer', ['store_id'], unique=False)
    op.create_table('jobsrecord',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('start_time', sa.DateTime(), nullable=True),
                    sa.Column('end_time', sa.DateTime(), nullable=True),
                    sa.Column('jobname', sa.String(length=100), nullable=False),
                    sa.Column('status', sa.String(length=50), nullable=False),
                    sa.Column('message', sa.String(length=100), nullable=True),
                    sa.Column('json_result', sa.String(length=150), nullable=True),
                    sa.Column('duration', sa.Integer(), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('lookup',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('created_on', sa.DateTime(), nullable=True),
                    sa.Column('updated_on', sa.DateTime(), nullable=True),
                    sa.Column('created_by', sa.String(length=50), nullable=True),
                    sa.Column('updated_by', sa.String(length=50), nullable=True),
                    sa.Column('store_id', sa.BigInteger(), nullable=False),
                    sa.Column('name', sa.String(length=100), nullable=False),
                    sa.Column('type', sa.String(length=100), nullable=False),
                    sa.Column('description', sa.String(length=100), nullable=True),
                    sa.Column('version', sa.Integer(), nullable=False),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_lookup_name'), 'lookup', ['name'], unique=False)
    op.create_index(op.f('ix_lookup_store_id'), 'lookup', ['store_id'], unique=False)
    op.create_table('lookupvalue',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('code', sa.String(length=100), nullable=False),
                    sa.Column('vendor_code', sa.String(length=100), nullable=True),
                    sa.Column('vendor_value', sa.String(length=200), nullable=True),
                    sa.Column('vendor_section', sa.String(length=200), nullable=True),
                    sa.Column('value', sa.String(length=200), nullable=True),
                    sa.Column('lookup_id', sa.BigInteger(), nullable=False),
                    sa.Column('parent_id', sa.BigInteger(), nullable=False),
                    sa.Column('order', sa.Integer(), nullable=True),
                    sa.Column('image_url', sa.String(length=500), nullable=True),
                    sa.Column('section', sa.String(length=50), nullable=True),
                    sa.Column('org_code', sa.String(length=100), nullable=True),
                    sa.Column('user_code', sa.String(length=100), nullable=True),
                    sa.Column('password', sa.String(length=100), nullable=True),
                    sa.Column('v_version', sa.String(length=100), nullable=True),
                    sa.Column('version', sa.Integer(), nullable=False),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_lookupvalue_lookup_id'), 'lookupvalue', ['lookup_id'], unique=False)
    op.create_index(op.f('ix_lookupvalue_parent_id'), 'lookupvalue', ['parent_id'], unique=False)
    op.create_table('release_history',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('created_on', sa.DateTime(), nullable=True),
                    sa.Column('updated_on', sa.DateTime(), nullable=True),
                    sa.Column('created_by', sa.String(length=50), nullable=True),
                    sa.Column('updated_by', sa.String(length=50), nullable=True),
                    sa.Column('app_id', sa.BigInteger(), nullable=True),
                    sa.Column('version', sa.String(length=50), nullable=True),
                    sa.Column('version_num', sa.Integer(), nullable=True),
                    sa.Column('note', sa.String(length=2000), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('role',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('created_on', sa.DateTime(), nullable=True),
                    sa.Column('updated_on', sa.DateTime(), nullable=True),
                    sa.Column('created_by', sa.String(length=50), nullable=True),
                    sa.Column('updated_by', sa.String(length=50), nullable=True),
                    sa.Column('title', sa.String(length=100), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_role_title'), 'role', ['title'], unique=True)
    op.create_table('sales_tracker',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('customer_id', sa.BigInteger(), nullable=False),
                    sa.Column('from_sales_id', sa.BigInteger(), nullable=False),
                    sa.Column('to_sales_id', sa.BigInteger(), nullable=False),
                    sa.Column('created_on', sa.DateTime(), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('status_tracker',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('model', sa.String(length=100), nullable=False),
                    sa.Column('model_id', sa.BigInteger(), nullable=True),
                    sa.Column('from_status', sa.String(length=50), nullable=False),
                    sa.Column('to_status', sa.String(length=50), nullable=False),
                    sa.Column('remark', sa.String(length=100), nullable=True),
                    sa.Column('parent_id', sa.BigInteger(), nullable=True),
                    sa.Column('duration_since_last_change', sa.Integer(), nullable=True),
                    sa.Column('created_on', sa.DateTime(), nullable=True),
                    sa.Column('created_by', sa.String(length=50), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('store',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('created_on', sa.DateTime(), nullable=True),
                    sa.Column('updated_on', sa.DateTime(), nullable=True),
                    sa.Column('created_by', sa.String(length=50), nullable=True),
                    sa.Column('updated_by', sa.String(length=50), nullable=True),
                    sa.Column('sequence_id', sa.String(length=100), nullable=True),
                    sa.Column('name', sa.String(length=250), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_store_name'), 'store', ['name'], unique=True)
    op.create_index(op.f('ix_store_sequence_id'), 'store', ['sequence_id'], unique=False)
    op.create_table('tasetting',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('created_on', sa.DateTime(), nullable=True),
                    sa.Column('updated_on', sa.DateTime(), nullable=True),
                    sa.Column('created_by', sa.String(length=50), nullable=True),
                    sa.Column('updated_by', sa.String(length=50), nullable=True),
                    sa.Column('store_id', sa.BigInteger(), nullable=False),
                    sa.Column('type', sa.String(length=50), nullable=True),
                    sa.Column('year', sa.Integer(), nullable=True),
                    sa.Column('month', sa.Integer(), nullable=True),
                    sa.Column('week', sa.Integer(), nullable=True),
                    sa.Column('sales_id', sa.BigInteger(), nullable=True),
                    sa.Column('value', sa.Integer(), nullable=True),
                    sa.Column('is_deleted', sa.Boolean(), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_tasetting_store_id'), 'tasetting', ['store_id'], unique=False)
    op.create_table('user',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('created_on', sa.DateTime(), nullable=True),
                    sa.Column('updated_on', sa.DateTime(), nullable=True),
                    sa.Column('created_by', sa.String(length=50), nullable=True),
                    sa.Column('updated_by', sa.String(length=50), nullable=True),
                    sa.Column('active', sa.Boolean(), nullable=True),
                    sa.Column('username', sa.String(length=50), nullable=True),
                    sa.Column('email', sa.String(length=50), nullable=True),
                    sa.Column('mobile', sa.String(length=50), nullable=True),
                    sa.Column('title', sa.String(length=200), nullable=True),
                    sa.Column('avatar', sa.String(length=200), nullable=True),
                    sa.Column('system', sa.String(length=200), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=False)
    op.create_index(op.f('ix_user_mobile'), 'user', ['mobile'], unique=False)
    op.create_table('customer',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('created_on', sa.DateTime(), nullable=True),
                    sa.Column('updated_on', sa.DateTime(), nullable=True),
                    sa.Column('created_by', sa.String(length=50), nullable=True),
                    sa.Column('updated_by', sa.String(length=50), nullable=True),
                    sa.Column('store_id', sa.BigInteger(), nullable=False),
                    sa.Column('last_tracker_id', sa.BigInteger(), nullable=True),
                    sa.Column('last_status_change_on', sa.DateTime(), nullable=True),
                    sa.Column('last_status_changer', sa.String(length=50), nullable=True),
                    sa.Column('name', sa.String(length=200), nullable=True),
                    sa.Column('mobile', sa.String(length=200), nullable=True),
                    sa.Column('gender', sa.Boolean(), nullable=True),
                    sa.Column('age_group', sa.String(length=50), nullable=True),
                    sa.Column('intent_car_ids', sa.String(length=200), nullable=True),
                    sa.Column('intent_car_series', sa.String(length=200), nullable=True),
                    sa.Column('intent_car_colors', sa.String(length=200), nullable=True),
                    sa.Column('test_drive_car_ids', sa.String(length=200), nullable=True),
                    sa.Column('intent_level', sa.String(length=50), nullable=True),
                    sa.Column('owned_car_ids', sa.String(length=200), nullable=True),
                    sa.Column('address_line', sa.String(length=500), nullable=True),
                    sa.Column('competing_car_ids', sa.String(length=200), nullable=True),
                    sa.Column('remark', sa.String(length=500), nullable=True),
                    sa.Column('channel', sa.String(length=50), nullable=True),
                    sa.Column('campaign_id', sa.BigInteger(), nullable=True),
                    sa.Column('is_refered', sa.Boolean(), nullable=True),
                    sa.Column('refered_info', sa.String(length=200), nullable=True),
                    sa.Column('is_company', sa.Boolean(), nullable=True),
                    sa.Column('company_name', sa.String(length=200), nullable=True),
                    sa.Column('defeated_reason', sa.String(length=500), nullable=True),
                    sa.Column('sales_id', sa.BigInteger(), nullable=False),
                    sa.Column('last_reception_date', sa.DateTime(), nullable=True),
                    sa.Column('next_appointment_date', sa.DateTime(), nullable=True),
                    sa.Column('birth_date', sa.Date(), nullable=True),
                    sa.Column('source', sa.String(length=20), nullable=True),
                    sa.Column('tags', sa.String(length=1024), nullable=True),
                    sa.Column('reassigned', sa.Boolean(), nullable=True),
                    sa.Column('plate_type', sa.String(length=200), nullable=True),
                    sa.Column('record_info', sa.String(length=500), nullable=True),
                    sa.Column('budget', sa.String(length=50), nullable=True),
                    sa.Column('payment', sa.String(length=50), nullable=True),
                    sa.Column('is_car_replace', sa.Boolean(), nullable=True),
                    sa.Column('license_loc', sa.String(length=50), nullable=True),
                    sa.Column('status', sa.String(length=50), nullable=False),
                    sa.ForeignKeyConstraint(['sales_id'], ['user.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_customer_sales_id'), 'customer', ['sales_id'], unique=False)
    op.create_index(op.f('ix_customer_store_id'), 'customer', ['store_id'], unique=False)
    op.create_table('store_user_role_scope',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('created_on', sa.DateTime(), nullable=True),
                    sa.Column('updated_on', sa.DateTime(), nullable=True),
                    sa.Column('created_by', sa.String(length=50), nullable=True),
                    sa.Column('updated_by', sa.String(length=50), nullable=True),
                    sa.Column('user_id', sa.BigInteger(), nullable=True),
                    sa.Column('store_id', sa.BigInteger(), nullable=True),
                    sa.Column('role_id', sa.BigInteger(), nullable=True),
                    sa.Column('scope_type', sa.String(length=50), nullable=False),
                    sa.Column('user_ids', sa.Text(), nullable=True),
                    sa.ForeignKeyConstraint(['role_id'], ['role.id'], ),
                    sa.ForeignKeyConstraint(['store_id'], ['store.id'], ),
                    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_store_user_role_scope_role_id'), 'store_user_role_scope', ['role_id'], unique=False)
    op.create_index(op.f('ix_store_user_role_scope_store_id'), 'store_user_role_scope', ['store_id'], unique=False)
    op.create_index(op.f('ix_store_user_role_scope_user_id'), 'store_user_role_scope', ['user_id'], unique=False)
    op.create_table('appointment',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('created_on', sa.DateTime(), nullable=True),
                    sa.Column('updated_on', sa.DateTime(), nullable=True),
                    sa.Column('created_by', sa.String(length=50), nullable=True),
                    sa.Column('updated_by', sa.String(length=50), nullable=True),
                    sa.Column('store_id', sa.BigInteger(), nullable=False),
                    sa.Column('last_tracker_id', sa.BigInteger(), nullable=True),
                    sa.Column('last_status_change_on', sa.DateTime(), nullable=True),
                    sa.Column('last_status_changer', sa.String(length=50), nullable=True),
                    sa.Column('customer_id', sa.BigInteger(), nullable=False),
                    sa.Column('sales_id', sa.BigInteger(), nullable=False),
                    sa.Column('appt_date', sa.Date(), nullable=True),
                    sa.Column('appt_datetime', sa.DateTime(), nullable=False),
                    sa.Column('remark', sa.String(length=500), nullable=True),
                    sa.Column('type', sa.String(length=50), nullable=False),
                    sa.Column('status', sa.String(length=50), nullable=False),
                    sa.ForeignKeyConstraint(['customer_id'], ['customer.id'], ),
                    sa.ForeignKeyConstraint(['sales_id'], ['user.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_appointment_appt_date'), 'appointment', ['appt_date'], unique=False)
    op.create_index(op.f('ix_appointment_store_id'), 'appointment', ['store_id'], unique=False)
    op.create_table('calllog',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('created_on', sa.DateTime(), nullable=True),
                    sa.Column('updated_on', sa.DateTime(), nullable=True),
                    sa.Column('created_by', sa.String(length=50), nullable=True),
                    sa.Column('updated_by', sa.String(length=50), nullable=True),
                    sa.Column('store_id', sa.BigInteger(), nullable=False),
                    sa.Column('customer_id', sa.BigInteger(), nullable=False),
                    sa.Column('mobile', sa.String(length=200), nullable=True),
                    sa.Column('appointment_id', sa.BigInteger(), nullable=True),
                    sa.Column('duration', sa.Integer(), nullable=False),
                    sa.Column('call_start', sa.DateTime(), nullable=False),
                    sa.Column('call_end', sa.DateTime(), nullable=True),
                    sa.Column('sales_id', sa.BigInteger(), nullable=False),
                    sa.Column('sequence_id', sa.String(length=100), nullable=True),
                    sa.ForeignKeyConstraint(['customer_id'], ['customer.id'], ),
                    sa.ForeignKeyConstraint(['sales_id'], ['user.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_calllog_store_id'), 'calllog', ['store_id'], unique=False)
    op.create_table('customer_addl_info',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('created_on', sa.DateTime(), nullable=True),
                    sa.Column('updated_on', sa.DateTime(), nullable=True),
                    sa.Column('created_by', sa.String(length=50), nullable=True),
                    sa.Column('updated_by', sa.String(length=50), nullable=True),
                    sa.Column('customer_id', sa.BigInteger(), nullable=True),
                    sa.Column('addl_contact_info', sa.String(length=200), nullable=True),
                    sa.Column('contact_time', sa.String(length=100), nullable=True),
                    sa.Column('industry', sa.String(length=100), nullable=True),
                    sa.Column('hobby', sa.String(length=100), nullable=True),
                    sa.Column('traits', sa.String(length=100), nullable=True),
                    sa.Column('car_service_life', sa.String(length=50), nullable=True),
                    sa.Column('car_mileage', sa.String(length=50), nullable=True),
                    sa.Column('has_used_car_assessed', sa.Boolean(), nullable=True),
                    sa.Column('used_car_value', sa.String(length=50), nullable=True),
                    sa.Column('district', sa.String(length=100), nullable=True),
                    sa.Column('dealership', sa.String(length=50), nullable=True),
                    sa.Column('purpose', sa.String(length=50), nullable=True),
                    sa.Column('actual_driver', sa.String(length=50), nullable=True),
                    sa.Column('drive_loc', sa.String(length=50), nullable=True),
                    sa.Column('trans_type', sa.String(length=50), nullable=True),
                    sa.ForeignKeyConstraint(['customer_id'], ['customer.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('drive_record',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('created_on', sa.DateTime(), nullable=True),
                    sa.Column('updated_on', sa.DateTime(), nullable=True),
                    sa.Column('created_by', sa.String(length=50), nullable=True),
                    sa.Column('updated_by', sa.String(length=50), nullable=True),
                    sa.Column('store_id', sa.BigInteger(), nullable=False),
                    sa.Column('customer_id', sa.BigInteger(), nullable=False),
                    sa.Column('sales_id', sa.BigInteger(), nullable=False),
                    sa.Column('car_code', sa.String(length=100), nullable=True),
                    sa.Column('start', sa.DateTime(), nullable=True),
                    sa.Column('end', sa.DateTime(), nullable=True),
                    sa.Column('duration', sa.Integer(), nullable=True),
                    sa.ForeignKeyConstraint(['customer_id'], ['customer.id'], ),
                    sa.ForeignKeyConstraint(['sales_id'], ['user.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_drive_record_store_id'), 'drive_record', ['store_id'], unique=False)
    op.create_table('order',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('created_on', sa.DateTime(), nullable=True),
                    sa.Column('updated_on', sa.DateTime(), nullable=True),
                    sa.Column('created_by', sa.String(length=50), nullable=True),
                    sa.Column('updated_by', sa.String(length=50), nullable=True),
                    sa.Column('store_id', sa.BigInteger(), nullable=False),
                    sa.Column('last_tracker_id', sa.BigInteger(), nullable=True),
                    sa.Column('last_status_change_on', sa.DateTime(), nullable=True),
                    sa.Column('last_status_changer', sa.String(length=50), nullable=True),
                    sa.Column('customer_id', sa.BigInteger(), nullable=False),
                    sa.Column('sales_id', sa.BigInteger(), nullable=False),
                    sa.Column('order_no', sa.String(length=100), nullable=True),
                    sa.Column('ordered_car_id', sa.String(length=100), nullable=False),
                    sa.Column('ordered_car_name', sa.String(length=100), nullable=False),
                    sa.Column('ordered_car_series', sa.String(length=100), nullable=True),
                    sa.Column('remark', sa.String(length=500), nullable=True),
                    sa.Column('is_confirmed', sa.Boolean(), nullable=True),
                    sa.Column('delivered_date', sa.Date(), nullable=True),
                    sa.Column('history_order', sa.Boolean(), nullable=True),
                    sa.Column('receipt_title', sa.String(length=500), nullable=True),
                    sa.Column('is_mortgage', sa.Boolean(), nullable=True),
                    sa.Column('include_insurance', sa.Boolean(), nullable=True),
                    sa.Column('invoice_price', sa.Numeric(precision=12, scale=2), nullable=True),
                    sa.Column('mortgage_amt', sa.Numeric(precision=12, scale=2), nullable=True),
                    sa.Column('finance_fee', sa.Numeric(precision=12, scale=2), nullable=True),
                    sa.Column('insurance_amt', sa.Numeric(precision=12, scale=2), nullable=True),
                    sa.Column('insurance_ext_amt', sa.Numeric(precision=12, scale=2), nullable=True),
                    sa.Column('service_fee', sa.Numeric(precision=12, scale=2), nullable=True),
                    sa.Column('prepaid_card_amt', sa.Numeric(precision=12, scale=2), nullable=True),
                    sa.Column('status', sa.String(length=50), nullable=False),
                    sa.ForeignKeyConstraint(['customer_id'], ['customer.id'], ),
                    sa.ForeignKeyConstraint(['sales_id'], ['user.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_order_store_id'), 'order', ['store_id'], unique=False)
    op.create_table('reception',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('created_on', sa.DateTime(), nullable=True),
                    sa.Column('updated_on', sa.DateTime(), nullable=True),
                    sa.Column('created_by', sa.String(length=50), nullable=True),
                    sa.Column('updated_by', sa.String(length=50), nullable=True),
                    sa.Column('store_id', sa.BigInteger(), nullable=False),
                    sa.Column('last_tracker_id', sa.BigInteger(), nullable=True),
                    sa.Column('last_status_change_on', sa.DateTime(), nullable=True),
                    sa.Column('last_status_changer', sa.String(length=50), nullable=True),
                    sa.Column('customer_id', sa.BigInteger(), nullable=False),
                    sa.Column('sales_id', sa.BigInteger(), nullable=False),
                    sa.Column('receptionist_id', sa.BigInteger(), nullable=True),
                    sa.Column('appointment_id', sa.BigInteger(), nullable=True),
                    sa.Column('people_count', sa.Integer(), nullable=False),
                    sa.Column('rx_type', sa.String(length=50), nullable=True),
                    sa.Column('orig_rx_type', sa.String(length=50), nullable=True),
                    sa.Column('order_id', sa.BigInteger(), nullable=True),
                    sa.Column('rx_date', sa.Date(), nullable=False),
                    sa.Column('rx_duration', sa.Integer(), nullable=True),
                    sa.Column('prev_rx_id', sa.BigInteger(), nullable=True),
                    sa.Column('status', sa.String(length=50), nullable=False),
                    sa.ForeignKeyConstraint(['customer_id'], ['customer.id'], ),
                    sa.ForeignKeyConstraint(['sales_id'], ['user.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_reception_rx_date'), 'reception', ['rx_date'], unique=False)
    op.create_index(op.f('ix_reception_store_id'), 'reception', ['store_id'], unique=False)
    # end create tables

    from application.nutils.csvloader import load_table_from_csv
    from application.nutils.csvloader import load_lookup_from_csv
    from application.nutils.csvloader import load_all_lookupvalue_from_csv

    load_table_from_csv(AppMeta.__tablename__, 'data/app.csv')
    load_lookup_from_csv('data/lookup.csv')
    load_all_lookupvalue_from_csv('data/lookupvalue', -1)


def downgrade():
    # start dropping tables and constraints
    op.drop_index(op.f('ix_reception_store_id'), table_name='reception')
    op.drop_index(op.f('ix_reception_rx_date'), table_name='reception')
    op.drop_table('reception')
    op.drop_index(op.f('ix_order_store_id'), table_name='order')
    op.drop_table('order')
    op.drop_index(op.f('ix_drive_record_store_id'), table_name='drive_record')
    op.drop_table('drive_record')
    op.drop_table('customer_addl_info')
    op.drop_index(op.f('ix_calllog_store_id'), table_name='calllog')
    op.drop_table('calllog')
    op.drop_index(op.f('ix_appointment_store_id'), table_name='appointment')
    op.drop_index(op.f('ix_appointment_appt_date'), table_name='appointment')
    op.drop_table('appointment')
    op.drop_index(op.f('ix_store_user_role_scope_user_id'), table_name='store_user_role_scope')
    op.drop_index(op.f('ix_store_user_role_scope_store_id'), table_name='store_user_role_scope')
    op.drop_index(op.f('ix_store_user_role_scope_role_id'), table_name='store_user_role_scope')
    op.drop_table('store_user_role_scope')
    op.drop_index(op.f('ix_customer_store_id'), table_name='customer')
    op.drop_index(op.f('ix_customer_sales_id'), table_name='customer')
    op.drop_table('customer')
    op.drop_index(op.f('ix_user_mobile'), table_name='user')
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.drop_table('user')
    op.drop_index(op.f('ix_tasetting_store_id'), table_name='tasetting')
    op.drop_table('tasetting')
    op.drop_index(op.f('ix_store_sequence_id'), table_name='store')
    op.drop_index(op.f('ix_store_name'), table_name='store')
    op.drop_table('store')
    op.drop_table('status_tracker')
    op.drop_table('sales_tracker')
    op.drop_index(op.f('ix_role_title'), table_name='role')
    op.drop_table('role')
    op.drop_table('release_history')
    op.drop_index(op.f('ix_lookupvalue_parent_id'), table_name='lookupvalue')
    op.drop_index(op.f('ix_lookupvalue_lookup_id'), table_name='lookupvalue')
    op.drop_table('lookupvalue')
    op.drop_index(op.f('ix_lookup_store_id'), table_name='lookup')
    op.drop_index(op.f('ix_lookup_name'), table_name='lookup')
    op.drop_table('lookup')
    op.drop_table('jobsrecord')
    op.drop_index(op.f('ix_hwjd_customer_store_id'), table_name='hwjd_customer')
    op.drop_table('hwjd_customer')
    op.drop_index(op.f('ix_frt_shared_inventory_store_id'), table_name='frt_shared_inventory')
    op.drop_table('frt_shared_inventory')
    op.drop_index(op.f('ix_frt_inventory_store_id'), table_name='frt_inventory')
    op.drop_table('frt_inventory')
    op.drop_index(op.f('ix_campaign_store_id'), table_name='campaign')
    op.drop_table('campaign')
    op.drop_table('app')
    # end dropping tables and constraints
