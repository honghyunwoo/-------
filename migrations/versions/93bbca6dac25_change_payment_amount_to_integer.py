"""change_payment_amount_to_integer

Revision ID: 93bbca6dac25
Revises: dc29c046ce38
Create Date: 2025-10-03 09:53:28.423089

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '93bbca6dac25'
down_revision: Union[str, Sequence[str], None] = 'dc29c046ce38'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - SQLite에서 컬럼 타입 변경 (테이블 재생성 방식)"""
    # SQLite는 ALTER COLUMN TYPE을 지원하지 않으므로 테이블 재생성 필요
    with op.batch_alter_table('payments', schema=None) as batch_op:
        batch_op.alter_column('amount',
                   existing_type=sa.FLOAT(),
                   type_=sa.Integer(),
                   existing_nullable=False)


def downgrade() -> None:
    """Downgrade schema"""
    with op.batch_alter_table('payments', schema=None) as batch_op:
        batch_op.alter_column('amount',
                   existing_type=sa.Integer(),
                   type_=sa.FLOAT(),
                   existing_nullable=False)
