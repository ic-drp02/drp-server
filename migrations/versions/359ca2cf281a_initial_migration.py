"""Initial migration

Revision ID: 359ca2cf281a
Revises:
Create Date: 2020-05-30 12:30:17.145176

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '359ca2cf281a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('posts',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('title', sa.String(length=120), nullable=False),
                    sa.Column('summary', sa.String(length=200), nullable=True),
                    sa.Column('content', sa.Text(), nullable=True),
                    sa.Column('created_at', sa.DateTime(timezone=True),
                              server_default=sa.text('now()'), nullable=False),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('tags',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(length=30), nullable=True),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('name')
                    )
    op.create_table('post_tag',
                    sa.Column('post_id', sa.Integer(), nullable=False),
                    sa.Column('tag_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ),
                    sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ),
                    sa.PrimaryKeyConstraint('post_id', 'tag_id')
                    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('post_tag')
    op.drop_table('tags')
    op.drop_table('posts')
    # ### end Alembic commands ###