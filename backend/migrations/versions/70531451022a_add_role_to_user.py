"""add_role_to_user

Revision ID: 70531451022a
Revises: 
Create Date: 2025-05-08 05:10:50.416490

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '70531451022a'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('role', sa.String(), nullable=True, server_default='user'))
    pass


def downgrade() -> None:
    op.drop_column('users', 'role')
    pass
