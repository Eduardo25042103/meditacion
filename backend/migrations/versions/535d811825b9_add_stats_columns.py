"""add_stats_columns

Revision ID: 535d811825b9
Revises: 70531451022a
Create Date: 2025-06-07 14:22:43.080119

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision: str = '535d811825b9'
down_revision: Union[str, None] = '70531451022a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('user_stats', sa.Column('total_sessions', sa.Integer(), nullable=True, default=0))
    op.add_column('user_stats', sa.Column('average_session_duration', sa.Float(), nullable=True, default=0.0))
    op.add_column('user_stats', sa.Column('last_updated', sa.DateTime(), nullable=True, default=datetime.utcnow))
    
    op.execute("UPDATE user_stats SET total_sessions = 0 WHERE total_sessions IS NULL")
    op.execute("UPDATE user_stats SET average_session_duration = 0.0 WHERE average_session_duration IS NULL")
    op.execute("UPDATE user_stats SET last_updated = CURRENT_TIMESTAMP WHERE last_updated IS NULL")

    op.alter_column('user_stats', 'total_sessions', nullable=False)
    op.alter_column('user_stats', 'average_session_duration', nullable=False)
    op.alter_column('user_stats', 'last_updated', nullable=False)
    pass


def downgrade() -> None:
    #Eliminar columnas agregadas
    op.drop_column('user_stats', 'last_updated')
    op.drop_column('user_stats', 'average_session_duration')
    op.drop_column('user_stats', 'total_sessions')
    pass
