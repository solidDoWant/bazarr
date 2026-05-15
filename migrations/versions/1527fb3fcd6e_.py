"""empty message

Revision ID: 1527fb3fcd6e
Revises: 309dc062d2e4
Create Date: 2026-05-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1527fb3fcd6e'
down_revision = '309dc062d2e4'
branch_labels = None
depends_on = None

bind = op.get_context().bind
insp = sa.inspect(bind)


def column_exists(table_name, column_name):
    columns = insp.get_columns(table_name)
    return any(c["name"] == column_name for c in columns)


def upgrade():
    if not column_exists('table_languages_profiles', 'alwaysUseWhisper'):
        with op.batch_alter_table('table_languages_profiles', schema=None) as batch_op:
            batch_op.add_column(sa.Column('alwaysUseWhisper', sa.Integer(), server_default='0'))


def downgrade():
    pass
