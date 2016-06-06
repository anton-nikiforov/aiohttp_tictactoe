from aiomysql.sa import create_engine
import sqlalchemy as sa

__all__ = ['users', 'games', 'games_users', 'games_moves']

metadata = sa.MetaData()

users = sa.Table('users', metadata,
                sa.Column('id', sa.Integer, primary_key=True),
                sa.Column('email', sa.String(255)),
                sa.Column('login', sa.String(255)),
                sa.Column('password', sa.String(255)))

games = sa.Table('games', metadata,
                sa.Column('id', sa.Integer, primary_key=True),
                sa.Column('created', sa.DateTime),
                sa.Column('finished', sa.DateTime),
                sa.Column('config_size', sa.Integer),
                sa.Column('winner_id', sa.Integer))

games_users = sa.Table('games_users', metadata,
                sa.Column('id', sa.Integer, primary_key=True),
                sa.Column('games_id', sa.Integer, sa.ForeignKey('games.id')),
                sa.Column('users_id', sa.Integer, sa.ForeignKey('users.id')))

games_moves = sa.Table('games_moves', metadata,
                sa.Column('id', sa.Integer, primary_key=True),
                sa.Column('games_id', sa.Integer, sa.ForeignKey('games.id')),
                sa.Column('users_id', sa.Integer, sa.ForeignKey('users.id')),
                sa.Column('x', sa.Integer),
                sa.Column('y', sa.Integer))

async def init_db(loop=None, host=None, db=None, user=None, password=None):
    engine = await create_engine(
        host=host,
        db=db,
        user=user,
        password=password,
        loop=loop,
        minsize=1,
        maxsize=5
        ) 
    return engine

class BaseModel():

    def __init__(self, db):
        self.db = db

    async def sql_transaction(self, sql):
        async with self.db.acquire() as conn:
            tr = await conn.begin()
            try:
                result = await conn.execute(sql)
            except Exception as e:
                print(str(e))
                await tr.rollback()
            else:
                await tr.commit()
                return result