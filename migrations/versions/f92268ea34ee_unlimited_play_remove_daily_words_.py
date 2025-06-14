"""Unlimited play: remove daily_words, update game_sessions for answer_word and game_mode

Revision ID: f92268ea34ee
Revises: 
Create Date: 2025-06-13 23:11:39.752874

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f92268ea34ee'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('daily_words', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_daily_words_date'))
        batch_op.drop_index(batch_op.f('ix_daily_words_date_mode'))
        batch_op.drop_index(batch_op.f('ix_daily_words_game_mode'))
        batch_op.drop_index(batch_op.f('ix_daily_words_word'))

    op.drop_table('daily_words')
    with op.batch_alter_table('game_sessions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('answer_word', sa.String(length=5), nullable=False))
        batch_op.add_column(sa.Column('game_mode', sa.Enum('CLASSIC', 'DISNEY', name='gamemode'), nullable=False))
        batch_op.drop_index(batch_op.f('ix_game_sessions_daily_word'))
        batch_op.drop_index(batch_op.f('ix_game_sessions_daily_word_id'))
        batch_op.drop_constraint(batch_op.f('uix_game_session_user_daily'), type_='unique')
        batch_op.create_index(batch_op.f('ix_game_sessions_answer_word'), ['answer_word'], unique=False)
        batch_op.create_index(batch_op.f('ix_game_sessions_game_mode'), ['game_mode'], unique=False)
        batch_op.create_index('ix_game_sessions_user_created', ['user_id', 'created_at'], unique=False)
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('daily_word_id')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('game_sessions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('daily_word_id', sa.INTEGER(), nullable=False))
        batch_op.create_foreign_key(None, 'daily_words', ['daily_word_id'], ['id'])
        batch_op.drop_index('ix_game_sessions_user_created')
        batch_op.drop_index(batch_op.f('ix_game_sessions_game_mode'))
        batch_op.drop_index(batch_op.f('ix_game_sessions_answer_word'))
        batch_op.create_unique_constraint(batch_op.f('uix_game_session_user_daily'), ['user_id', 'daily_word_id'])
        batch_op.create_index(batch_op.f('ix_game_sessions_daily_word_id'), ['daily_word_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_game_sessions_daily_word'), ['daily_word_id'], unique=False)
        batch_op.drop_column('game_mode')
        batch_op.drop_column('answer_word')

    op.create_table('daily_words',
    sa.Column('word', sa.VARCHAR(length=5), nullable=False),
    sa.Column('game_mode', sa.VARCHAR(length=7), nullable=False),
    sa.Column('date', sa.DATE(), nullable=False),
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('created_at', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('date', 'game_mode', name=op.f('uix_daily_word_date_mode'))
    )
    with op.batch_alter_table('daily_words', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_daily_words_word'), ['word'], unique=False)
        batch_op.create_index(batch_op.f('ix_daily_words_game_mode'), ['game_mode'], unique=False)
        batch_op.create_index(batch_op.f('ix_daily_words_date_mode'), ['date', 'game_mode'], unique=False)
        batch_op.create_index(batch_op.f('ix_daily_words_date'), ['date'], unique=False)

    # ### end Alembic commands ###
