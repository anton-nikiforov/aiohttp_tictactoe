from aiohttp import web
from aiohttp_session import get_session

from auth.models import User
from settings import *


async def db_handler(app, handler):
    async def middleware(request):
        if request.path.startswith('/static/') or request.path.startswith('/_debugtoolbar'):
            response = await handler(request)
            return response
        request.db = app.db
        response = await handler(request)
        return response
    return middleware

async def authorize(app, handler):
    async def middleware(request):
        def check_path(path):
            result = True
            for r in ['/login', '/static/', '/signin', '/signout', '/_debugtoolbar/']:
                if path.startswith(r):
                    result = False
            return result
        session = await get_session(request)
        if session.get("user"):
            app.is_authorized=True
            user_instance = User(app.db)
            app.user = await user_instance.one(int(session.get("user")))
            return await handler(request)
        elif check_path(request.path):
            app.is_authorized=False
            url = request.app.router['login'].url()
            raise web.HTTPFound(url)
            return handler(request)
        else:
            app.is_authorized=False
            return await handler(request)
    return middleware