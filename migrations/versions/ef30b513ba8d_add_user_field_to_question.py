"""Add user field to question

Revision ID: ef30b513ba8d
Revises: e4a7313347a8
Create Date: 2020-06-11 08:26:10.266163

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ef30b513ba8d'
down_revision = 'e4a7313347a8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('questions', sa.Column(
        'user_id', sa.Integer(), nullable=True))
    op.create_foreign_key("questions_user_id_fkey", 'questions',
                          'users', ['user_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("questions_user_id_fkey",
                       'questions', type_='foreignkey')
    op.drop_column('questions', 'user_id')
    # ### end Alembic commands ###
