"""Production Auth v1: public_id, refresh_tokens, otp_challenges

Revision ID: 028_production_auth_v1
Revises: 027_square_order_lookup_and_fee_ledger
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite, postgresql

# revision identifiers, used by Alembic.
revision = '028_production_auth_v1'
down_revision = '027_square_order_lookup_and_fee_ledger'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == 'sqlite'
    
    # Determine UUID type based on database
    if is_sqlite:
        uuid_type = sa.String(36)  # SQLite uses TEXT for UUIDs
    else:
        uuid_type = postgresql.UUID(as_uuid=False)
    
    # 1. Add public_id to users table
    try:
        op.add_column('users', sa.Column('public_id', uuid_type, nullable=True))
        
        # Generate UUIDs for existing users (SQLite-compatible)
        if is_sqlite:
            # SQLite: Generate UUIDs using Python
            import uuid
            conn = bind.connect()
            users = conn.execute(sa.text("SELECT id FROM users")).fetchall()
            for user_id in users:
                new_uuid = str(uuid.uuid4())
                conn.execute(sa.text("UPDATE users SET public_id = :uuid WHERE id = :id"), 
                           {"uuid": new_uuid, "id": user_id[0]})
            conn.commit()
            conn.close()
        else:
            # PostgreSQL: Use gen_random_uuid()
            op.execute("UPDATE users SET public_id = gen_random_uuid() WHERE public_id IS NULL")
        
        # Make public_id NOT NULL and unique
        op.alter_column('users', 'public_id', nullable=False)
        op.create_unique_constraint('uq_users_public_id', 'users', ['public_id'])
        op.create_index('ix_users_public_id', 'users', ['public_id'], unique=True)
    except Exception as e:
        # Column might already exist - skip
        print(f"Note: public_id column may already exist: {e}")
        pass
    
    # 2. Update users table: make email nullable, add phone, update auth_provider constraints
    try:
        # Make email nullable (for phone-only users)
        op.alter_column('users', 'email', nullable=True)
        
        # Add phone column (E.164 format)
        op.add_column('users', sa.Column('phone', sa.String(), nullable=True))
        
        # Rename oauth_sub to provider_sub for clarity
        try:
            op.alter_column('users', 'oauth_sub', new_column_name='provider_sub')
        except Exception:
            # Column might already be named provider_sub
            pass
        
        # Ensure provider_sub exists
        try:
            op.add_column('users', sa.Column('provider_sub', sa.String(), nullable=True))
        except Exception:
            pass
        
        # Update auth_provider default if needed
        op.alter_column('users', 'auth_provider', server_default='local', nullable=False)
    except Exception as e:
        print(f"Note: users table updates may have issues: {e}")
        pass
    
    # 3. Create unique constraints on users
    try:
        # Unique constraint on (auth_provider, provider_sub) where provider_sub is not null
        # SQLite doesn't support partial unique indexes, so we'll enforce at application level
        # But we can still create the index for PostgreSQL
        if not is_sqlite:
            op.create_index(
                'ix_users_auth_provider_sub',
                'users',
                ['auth_provider', 'provider_sub'],
                unique=True,
                postgresql_where=sa.text('provider_sub IS NOT NULL')
            )
        else:
            # SQLite: create non-unique index, enforce uniqueness in application
            op.create_index('ix_users_auth_provider_sub', 'users', ['auth_provider', 'provider_sub'])
        
        # Unique index on email where not null (application-level enforcement for SQLite)
        if not is_sqlite:
            op.create_index(
                'ix_users_email_unique',
                'users',
                ['email'],
                unique=True,
                postgresql_where=sa.text('email IS NOT NULL')
            )
        else:
            # SQLite: email already has unique constraint from original schema
            pass
        
        # Unique index on phone where not null
        if not is_sqlite:
            op.create_index(
                'ix_users_phone_unique',
                'users',
                ['phone'],
                unique=True,
                postgresql_where=sa.text('phone IS NOT NULL')
            )
        else:
            op.create_index('ix_users_phone_unique', 'users', ['phone'], unique=True)
    except Exception as e:
        print(f"Note: unique constraints may have issues: {e}")
        pass
    
    # 4. Create refresh_tokens table
    op.create_table(
        'refresh_tokens',
        sa.Column('id', uuid_type, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('replaced_by', uuid_type, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['replaced_by'], ['refresh_tokens.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes on refresh_tokens
    op.create_index('ix_refresh_tokens_user_id', 'refresh_tokens', ['user_id'])
    op.create_index('ix_refresh_tokens_expires_at', 'refresh_tokens', ['expires_at'])
    op.create_index('ix_refresh_tokens_token_hash', 'refresh_tokens', ['token_hash'], unique=True)
    op.create_index('ix_refresh_tokens_revoked', 'refresh_tokens', ['revoked'])
    
    # 5. Create otp_challenges table
    op.create_table(
        'otp_challenges',
        sa.Column('id', uuid_type, nullable=False),
        sa.Column('phone', sa.String(), nullable=False),
        sa.Column('code_hash', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_attempts', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('consumed', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes on otp_challenges
    op.create_index('ix_otp_challenges_phone_expires', 'otp_challenges', ['phone', 'expires_at'])
    op.create_index('ix_otp_challenges_phone_consumed', 'otp_challenges', ['phone', 'consumed'])
    op.create_index('ix_otp_challenges_expires_at', 'otp_challenges', ['expires_at'])


def downgrade():
    # Drop otp_challenges table
    try:
        op.drop_index('ix_otp_challenges_expires_at', table_name='otp_challenges')
        op.drop_index('ix_otp_challenges_phone_consumed', table_name='otp_challenges')
        op.drop_index('ix_otp_challenges_phone_expires', table_name='otp_challenges')
        op.drop_table('otp_challenges')
    except Exception:
        pass
    
    # Drop refresh_tokens table
    try:
        op.drop_index('ix_refresh_tokens_revoked', table_name='refresh_tokens')
        op.drop_index('ix_refresh_tokens_token_hash', table_name='refresh_tokens')
        op.drop_index('ix_refresh_tokens_expires_at', table_name='refresh_tokens')
        op.drop_index('ix_refresh_tokens_user_id', table_name='refresh_tokens')
        op.drop_table('refresh_tokens')
    except Exception:
        pass
    
    # Revert users table changes
    try:
        op.drop_index('ix_users_phone_unique', table_name='users')
        op.drop_index('ix_users_email_unique', table_name='users')
        op.drop_index('ix_users_auth_provider_sub', table_name='users')
        op.drop_column('users', 'phone')
        op.alter_column('users', 'email', nullable=False)
        op.drop_index('ix_users_public_id', table_name='users')
        op.drop_constraint('uq_users_public_id', 'users', type_='unique')
        op.drop_column('users', 'public_id')
    except Exception:
        pass

