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
		return await self.sql_transaction(games.insert().values(
			created=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
			config_size=data['size']))

	async def add_user(self, users_id=None, games_id=None):
		return await self.sql_transaction(games_users.insert().values(
								users_id=users_id, games_id=games_id))

	async def all(self):
		async with self.db.acquire() as conn:
			result = await conn.execute('''
				select g.*, (select count(gu.id) from games_users gu 
							where gu.games_id = g.id) as users_count,
					(select group_concat(u.login order by gu.id separator ', ') 
						from users u
						left join games_users gu on u.id = gu.users_id 
						where gu.games_id = g.id
					) as users_login,
					(select group_concat(u.id separator ',') from users u
						left join games_users gu on u.id = gu.users_id 
						where gu.games_id = g.id
					) as users_ids,
					(select u.login from users u where u.id = g.winner_id) 
						as winner_login
				from games g order by g.created desc;''')
			return await result.fetchall()

	async def one(self, game_id=None):
		async with self.db.acquire() as conn:
			result = await conn.execute(games.select().where(games.c.id == game_id))
			return await result.first()

	async def get_users(self, game_id=None):
		async with self.db.acquire() as conn:
			result = await conn.execute('''select u.* from users u 
				left join games_users gu on gu.users_id = u.id 
				where games_id={} order by gu.id;'''.format(game_id))
			return await result.fetchall()

	async def get_moves(self, game_id=None):
		async with self.db.acquire() as conn:
			result = await conn.execute(games_moves.select(
										games_moves.c.games_id == game_id))
			return await result.fetchall()

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

	async def save_move(self, users_id=None, games_id=None, x=None, y=None):
		return await self.sql_transaction(games_moves.insert().values(
						users_id=users_id, games_id=games_id, x=x, y=y))

	async def finish_game(self, games_id=None, users_id=None):
		finished = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		return await self.sql_transaction(games.update() \
						.where(games.c.id == games_id) \
						.values(winner_id=users_id, finished=finished))