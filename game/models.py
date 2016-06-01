from datetime import datetime

from database import games, games_users

class Games():
	
	def __init__(self, db):
		self.db = db

	async def create(self, data=None):
        async with self.db.acquire() as conn:
            tr = await conn.begin()
            result = await conn.execute(games.insert().values(
                created=datetime(),
         		config_size=data['size']
                ))
            await tr.commit()
            return result

    async def add_user(self, users_id=None, games_id=None):
     	async with self.db.acquire() as conn:
            tr = await conn.begin()
            result = await conn.execute(games_users.insert().values(
                users_id=users_id,
         		games_id=games_id
                ))
            await tr.commit()
            return result   	

class Message():

	def __init__(self, db):
		self.db = db

	async def save(self, user, msg, **kw):
		return False

	async def get_messages(self):
		return False