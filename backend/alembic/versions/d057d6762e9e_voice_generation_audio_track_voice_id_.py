"""voice generation: audio_track, voice_id, content_hash on generations

Revision ID: d057d6762e9e
Revises: e8286dcd42dc
Create Date: 2026-08-08 02:23:19.159303

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd057d6762e9e'
down_revision: Union[str, None] = 'e8286dcd42dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLite can't ALTER a table to add a constraint in place - batch mode
    # does the copy-and-move rebuild Alembic's SQLite dialect needs for the
    # new foreign key. Split into separate batches (rather than one with
    # every add_column/create_index/create_foreign_key together): batching
    # multiple new columns' indexes in the same pass as the column adds trips
    # a CircularDependencyError in Alembic's batch column-reordering.
    with op.batch_alter_table("generations") as batch_op:
        batch_op.add_column(
            sa.Column("audio_track", sa.Enum("DIALOGUE", "NARRATION", name="audiotrack"), nullable=True)
        )
        batch_op.add_column(sa.Column("voice_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("content_hash", sa.String(length=64), nullable=True))

    with op.batch_alter_table("generations") as batch_op:
        batch_op.create_index(batch_op.f("ix_generations_content_hash"), ["content_hash"], unique=False)
        batch_op.create_index(batch_op.f("ix_generations_voice_id"), ["voice_id"], unique=False)
        batch_op.create_foreign_key("fk_generations_voice_id_voices", "voices", ["voice_id"], ["id"])


def downgrade() -> None:
    with op.batch_alter_table("generations") as batch_op:
        batch_op.drop_constraint("fk_generations_voice_id_voices", type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_generations_voice_id"))
        batch_op.drop_index(batch_op.f("ix_generations_content_hash"))

    with op.batch_alter_table("generations") as batch_op:
        batch_op.drop_column("content_hash")
        batch_op.drop_column("voice_id")
        batch_op.drop_column("audio_track")
