"""Set question user to null on user delete

Revision ID: b70448119cda
Revises: ef30b513ba8d
Create Date: 2020-06-14 21:08:53.120286

"""
from alembic import op
# import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b70448119cda'
down_revision = 'ef30b513ba8d'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("questions_user_id_fkey",
                       "questions", type_="foreignkey")
    op.create_foreign_key("questions_user_id_fkey", 'questions',
                          'users', ['user_id'], ['id'], ondelete="SET NULL")


def downgrade():
    op.drop_constraint("questions_user_id_fkey",
                       "questions", type_="foreignkey")
    op.create_foreign_key("questions_user_id_fkey", 'questions',
                          'users', ['user_id'], ['id'])
