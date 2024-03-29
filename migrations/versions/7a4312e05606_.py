"""empty message

Revision ID: 7a4312e05606
Revises: ce3088032520
Create Date: 2020-02-29 14:05:46.584931

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7a4312e05606'
down_revision = 'ce3088032520'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('users', 'email',
               existing_type=sa.VARCHAR(length=50),
               nullable=True)
    op.alter_column('users', 'firstname',
               existing_type=sa.VARCHAR(length=50),
               nullable=True)
    op.alter_column('users', 'lastname',
               existing_type=sa.VARCHAR(length=50),
               nullable=True)
    op.alter_column('users', 'password',
               existing_type=sa.VARCHAR(length=50),
               nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('users', 'password',
               existing_type=sa.VARCHAR(length=50),
               nullable=False)
    op.alter_column('users', 'lastname',
               existing_type=sa.VARCHAR(length=50),
               nullable=False)
    op.alter_column('users', 'firstname',
               existing_type=sa.VARCHAR(length=50),
               nullable=False)
    op.alter_column('users', 'email',
               existing_type=sa.VARCHAR(length=50),
               nullable=False)
    # ### end Alembic commands ###
