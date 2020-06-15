"""Remove tag name limit

Revision ID: 88c687971a14
Revises: b70448119cda
Create Date: 2020-06-15 16:50:15.271859

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '88c687971a14'
down_revision = 'b70448119cda'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("tags", "name", existing_type=sa.String(30), type_=sa.Text)


def downgrade():
    op.alter_column("tags", "name", existing_type=sa.Text, type_=sa.String(30))
