"""conversations and messages

Revision ID: f2a8b3c4d5e6
Revises: e4b7a9c3d1f2
Create Date: 2026-10-09 02:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "f2a8b3c4d5e6"
down_revision: str | None = "b7c8d9e0f1a2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_MESSAGE_KIND = sa.Enum(
    "text", "attachment", "meeting", name="messagekind", native_enum=False, length=16
)


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["candidate_id"],
            ["candidate_profiles.id"],
            name=op.f("fk_conversations_candidate_id_candidate_profiles"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name=op.f("fk_conversations_company_id_companies"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conversations")),
        sa.UniqueConstraint("company_id", "candidate_id", name=op.f("uq_conversations_company_id")),
    )
    op.create_index(op.f("ix_conversations_company_id"), "conversations", ["company_id"])
    op.create_index(op.f("ix_conversations_candidate_id"), "conversations", ["candidate_id"])
    op.create_index(op.f("ix_conversations_last_message_at"), "conversations", ["last_message_at"])

    op.create_table(
        "message_attachments",
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("uploader_id", sa.Uuid(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("media_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("storage_key", sa.String(length=500), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            name=op.f("fk_message_attachments_conversation_id_conversations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["uploader_id"],
            ["users.id"],
            name=op.f("fk_message_attachments_uploader_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_message_attachments")),
    )
    op.create_index(
        op.f("ix_message_attachments_conversation_id"), "message_attachments", ["conversation_id"]
    )

    op.create_table(
        "messages",
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("sender_id", sa.Uuid(), nullable=False),
        sa.Column("kind", _MESSAGE_KIND, nullable=False),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("attachment_id", sa.Uuid(), nullable=True),
        sa.Column("meeting_id", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["attachment_id"],
            ["message_attachments.id"],
            name=op.f("fk_messages_attachment_id_message_attachments"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            name=op.f("fk_messages_conversation_id_conversations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["meeting_id"],
            ["meetings.id"],
            name=op.f("fk_messages_meeting_id_meetings"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["sender_id"],
            ["users.id"],
            name=op.f("fk_messages_sender_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_messages")),
    )
    op.create_index(op.f("ix_messages_conversation_id"), "messages", ["conversation_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_messages_conversation_id"), table_name="messages")
    op.drop_table("messages")
    op.drop_index(op.f("ix_message_attachments_conversation_id"), table_name="message_attachments")
    op.drop_table("message_attachments")
    op.drop_index(op.f("ix_conversations_last_message_at"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_candidate_id"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_company_id"), table_name="conversations")
    op.drop_table("conversations")
