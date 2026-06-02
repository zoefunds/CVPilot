"""email verification: users.email_verified_at + email_verification_tokens

Revision ID: b1f7f97975fe
Revises: dc57be745ccf
Create Date: 2026-06-01 08:00:00.000000

Backfills email_verified_at = created_at for every pre-existing user, so
existing accounts aren't locked out by the new verification gate.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'b1f7f97975fe'
down_revision: str | None = 'dc57be745ccf'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Column.
    op.add_column(
        'users',
        sa.Column('email_verified_at', sa.DateTime(timezone=True), nullable=True),
    )
    # 2. Grandfather: every existing user is treated as verified.
    op.execute("UPDATE users SET email_verified_at = created_at WHERE email_verified_at IS NULL")

    # 3. Verification tokens table.
    op.create_table(
        'email_verification_tokens',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('token_hash', sa.String(length=128), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.id'],
            name=op.f('fk_email_verification_tokens_user_id_users'),
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_email_verification_tokens')),
        sa.UniqueConstraint('token_hash', name=op.f('uq_email_verification_tokens_token_hash')),
    )
    op.create_index(
        op.f('ix_email_verification_tokens_user_id'),
        'email_verification_tokens',
        ['user_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_email_verification_tokens_token_hash'),
        'email_verification_tokens',
        ['token_hash'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_email_verification_tokens_token_hash'), table_name='email_verification_tokens')
    op.drop_index(op.f('ix_email_verification_tokens_user_id'), table_name='email_verification_tokens')
    op.drop_table('email_verification_tokens')
    op.drop_column('users', 'email_verified_at')
