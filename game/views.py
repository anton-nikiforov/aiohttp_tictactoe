import aiohttp_jinja2
from aiohttp_session import get_session
from aiohttp import web, MsgType

from auth.models import User
from game.forms import GameCreateForm
from game.models import Games, Message
from settings import log, PLAYERS_IN_GAME
from utils import redirect

@aiohttp_jinja2.template('game/create.html')
async def games_create(request):
    ''' Create new game '''
    session = await get_session(request)
    form = GameCreateForm()
    if request.method == 'POST':
        form.process(await request.post())
        if form.validate():
            games = Games(request.db)
            result = await games.create(form.data)
            if result and result.lastrowid:
                await games_join_helper(request, result.lastrowid)
    return {'title': 'List of games', 'form': form}

async def games_join(request):
    ''' Join game and redirect to play '''
    await games_join_helper(request, request.match_info['id'])

async def games_join_helper(request, game_id=None):
    ''' Join game helper function '''
    games = Games(request.db)
    count_players = await games.count_users_in_game(game_id)

    if count_players >= PLAYERS_IN_GAME:
        print('Game has already {} players.'.format(PLAYERS_IN_GAME))
        raise web.HTTPFound(request.app.router['main'].url())   

    session = await get_session(request)
    user_id = int(session['user'])
    is_user_in_game = await games.is_user_in_game(user_id, game_id)

    if is_user_in_game:
        print('User #{} is already in game #{}'.format(user_id, game_id))
        raise web.HTTPFound(request.app.router['main'].url())

    await games.add_user(user_id, game_id)
    raise web.HTTPFound(request.app.router['game_detail'].url(parts={'id': game_id}))   

@aiohttp_jinja2.template('game/index.html')
async def games_list(request):
    ''' List of games '''
    session = await get_session(request)
    user_id = int(session['user'])
    games = Games(request.db)
    result = await games.all()
    data = []

    for one in result:
        data_one = dict(one)
        data_one['detail_url'] = request.app.router['game_detail'].url(parts={'id': one.id})
        data_one['join_url'] = request.app.router['game_join'].url(parts={'id': one.id})
        data.append(data_one)

    return {'title': 'List of games', 'data': data}

@aiohttp_jinja2.template('game/detail.html')
async def games_detail(request):
    ''' Play or watch game '''
    game_id = request.match_info['id']

    games = Games(request.db)
    game_info = await games.one(game_id)
    game_users = await games.get_users(game_id)
    game_moves = await games.get_moves(game_id)

    return {
        'game_id': game_id,
        'game_info': game_info,
        'game_users': game_users,
        'game_moves': game_moves,
        'title': 'Game room #{}'.format(game_id)
    }

class WebSocket(web.View):
    
    async def get(self):
        ws = web.WebSocketResponse()
        await ws.prepare(self.request)

        session = await get_session(self.request)
        user = User(self.request.db, {'id': session.get('user')})
        login = await user.get_login()

        for _ws in self.request.app['websockets']:
            _ws.send_str('%s joined' % login)
        self.request.app['websockets'].append(ws)

        async for msg in ws:
            if msg.tp == MsgType.text:
                if msg.data == 'close':
                    await ws.close()
                else:
                    message = Message(self.request.db)
                    result = await message.save(user=login, msg=msg.data)
                    log.debug(result)
                    for _ws in self.request.app['websockets']:
                        _ws.send_str('(%s) %s' % (login, msg.data))
            elif msg.tp == MsgType.error:
                log.debug('ws connection closed with exception %s' % ws.exception())

        self.request.app['websockets'].remove(ws)
        for _ws in self.request.app['websockets']:
            _ws.send_str('%s disconected' % login)
        log.debug('websocket connection closed')

        return ws