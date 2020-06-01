"""Add files

Revision ID: 827fd7886320
Revises: 359ca2cf281a
Create Date: 2020-06-01 09:37:08.457752

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '827fd7886320'
down_revision = '359ca2cf281a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('files',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(length=200), nullable=True),
                    sa.Column('filename', sa.String(
                        length=300), nullable=True),
                    sa.Column('post_id', sa.Integer(), nullable=True),
                    sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('files')
    # ### end Alembic commands ###