import json
from collections import defaultdict

import asyncio
import aiohttp_jinja2
import aiohttp_debugtoolbar
import jinja2
from aiohttp_session import session_middleware
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from aiohttp import web

from database import init_db
from middlewares import db_handler, authorize
from routes import routes
from settings import *
from utils import PeriodicTask


async def on_shutdown(app):
    for key, game in app['websockets'].items():
        for ws in game:
            await ws.close(code=1001, message='Server shutdown')

async def shutdown(server, app, handler):
    server.close()
    await server.wait_closed()
    app.db.close()
    await app.db.wait_closed()
    await app.shutdown()
    await handler.finish_connections(10.0)
    await app.cleanup()


async def init(loop):
    app = web.Application(loop=loop, middlewares=[
        session_middleware(EncryptedCookieStorage(SECRET_KEY)),
        authorize,
        db_handler,
        aiohttp_debugtoolbar.middleware,
    ])
    app['websockets'] = defaultdict(list)
    handler = app.make_handler()
    if DEBUG:
        aiohttp_debugtoolbar.setup(app, intercept_redirects=False)
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('templates'))

    # route part
    for route in routes:
        app.router.add_route(route[0], route[1], route[2], name=route[3])
    app.router.add_static('/static', 'static', name='static')
    # end route part
    # db connect
    app.db = await init_db(
        host=MYSQL_HOST,
        db=MYSQL_DB_NAME,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        loop=loop
        )
    # end db connect
    app.on_shutdown.append(on_shutdown)

    serv_generator = loop.create_server(handler, SITE_HOST, SITE_PORT)
    return serv_generator, handler, app

def ws_interval(app=None):
    ''' Send to all users empty message to avoid nginx timeout '''
    for key, game in app['websockets'].items():
        for ws in game:
            ws.send_str(json.dumps({'message': 'pong', 
                                    'status': STATUS['INFO']}))

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    serv_generator, handler, app = loop.run_until_complete(init(loop))
    serv = loop.run_until_complete(serv_generator)
    # Create periodic task
    task = PeriodicTask(lambda: ws_interval(app), PONG_WS_INTERVAL)
    log.debug('start server %s' % str(serv.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        log.debug('Stop server begin')
    finally:
        loop.run_until_complete(shutdown(serv, app, handler))
        loop.close()
    log.debug('Stop server end')