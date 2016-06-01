from database import users

class User():
    
    def __init__(self, db):
        self.db = db

    async def check_email(self, email=None):
        async with self.db.acquire() as conn:
            return await conn.execute(users.select(users.c.email == email))

    async def authenticate(self, email=None, password=None):
        async with self.db.acquire() as conn:
            return await conn.execute(users.select().where(users.c.email == email).where(users.c.password == password))        

    async def save(self, data=None):
        async with self.db.acquire() as conn:
            tr = await conn.begin()
            result = await conn.execute(users.insert().values(
                login=data['login'],
                email=data['email'],
                password=data['password']
                ))
            await tr.commit()
            return result
