"""password_reset_tokens

Revision ID: dc57be745ccf
Revises: b74a37017d63
Create Date: 2026-06-01 06:35:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'dc57be745ccf'
down_revision: str | None = 'b74a37017d63'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'password_reset_tokens',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('token_hash', sa.String(length=128), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.id'],
            name=op.f('fk_password_reset_tokens_user_id_users'),
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_password_reset_tokens')),
        sa.UniqueConstraint('token_hash', name=op.f('uq_password_reset_tokens_token_hash')),
    )
    op.create_index(
        op.f('ix_password_reset_tokens_user_id'),
        'password_reset_tokens',
        ['user_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_password_reset_tokens_token_hash'),
        'password_reset_tokens',
        ['token_hash'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_password_reset_tokens_token_hash'), table_name='password_reset_tokens')
    op.drop_index(op.f('ix_password_reset_tokens_user_id'), table_name='password_reset_tokens')
    op.drop_table('password_reset_tokens')
