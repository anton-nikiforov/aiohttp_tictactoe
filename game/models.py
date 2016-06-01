from datetime import datetime

from database import (
	BaseModel, 
	games, 
	games_users
	)

class Games(BaseModel):

	async def create(self, data=None):
		return await self.insert(games.insert().values(
			created=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
			config_size=data['size']))

	async def add_user(self, users_id=None, games_id=None):
		return await self.insert(games_users.insert().values(
								users_id=users_id, games_id=games_id))

class Message():

	def __init__(self, db):
		self.db = db

	async def save(self, user, msg, **kw):
		return False

	async def get_messages(self):
		return False