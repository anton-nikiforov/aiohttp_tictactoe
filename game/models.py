from datetime import datetime

from sqlalchemy import select

from database import (
	BaseModel, 
	games, 
	games_moves,
	games_users,
	users
	)

class Games(BaseModel):

	async def create(self, data=None):
		return await self.insert(games.insert().values(
			created=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
			config_size=data['size']))

	async def add_user(self, users_id=None, games_id=None):
		return await self.insert(games_users.insert().values(
								users_id=users_id, games_id=games_id))

	async def all(self):
		async with self.db.acquire() as conn:
			return await conn.execute('''
				select g.*, (select count(gu.id) from games_users gu 
							where gu.games_id = g.id) as users_count,
					(select group_concat(u.login separator ', ') from users u
						left join games_users gu on u.id = gu.users_id 
						left join games gg on gg.id = gu.games_id 
						where gg.id = g.id
					) as users_login
				from games g order by g.created desc''')

	async def one(self, game_id=None):
		async with self.db.acquire() as conn:
			return await conn.execute(games.select(games.c.id == game_id))

	async def get_users(self, game_id=None):
		stm = select([games_users.c.users_id]).where(games_users.c.games_id == game_id)
		async with self.db.acquire() as conn:
			return await conn.execute(users.select().where(users.c.id == stm))

	async def get_moves(self, game_id=None):
		async with self.db.acquire() as conn:
			return await conn.execute(games_moves.select(
										games_moves.c.games_id == game_id))

	async def count_users_in_game(self, game_id=None):
		async with self.db.acquire() as conn:
			result = await conn.execute(games_users.count().where(games_users.c.games_id == game_id))
			return await result.scalar()		

	async def is_user_in_game(self, users_id=None, games_id=None):
		async with self.db.acquire() as conn:
			result = await conn.execute(games_users.count() \
							.where(games_users.c.games_id == games_id) \
							.where(games_users.c.users_id == users_id))
			return await result.scalar()

class Message():

	def __init__(self, db):
		self.db = db

	async def save(self, user, msg, **kw):
		return False

	async def get_messages(self):
		return False