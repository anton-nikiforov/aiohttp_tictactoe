import json

import aiohttp_jinja2
from aiohttp_session import get_session
from aiohttp import web, MsgType

from auth.models import User
from game.forms import GameCreateForm
from game.models import Games
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
        if one.users_count < PLAYERS_IN_GAME and \
                user_id not in list(map(int, one.users_ids.split(','))):
            data_one['url'] = request.app.router['game_join'].url(parts={'id': one.id})
            data_one['url_label'] = 'Join'
        else:
            data_one['url'] = request.app.router['game_detail'].url(parts={'id': one.id})
            data_one['url_label'] = 'View'           
        data.append(data_one)

    return {'title': 'List of games', 'data': data}

@aiohttp_jinja2.template('game/detail.html')
async def games_detail(request):
    ''' Play or watch game '''
    session = await get_session(request)
    user_id = int(session['user'])

    game_id = request.match_info['id']

    games = Games(request.db)
    game_info = await games.one(game_id)
    game_users = await games.get_users(game_id)
    game_moves = await games.get_moves(game_id)

    current_user_in_game = any(user.id == user_id for user in game_users)

    return {
        'game_id': game_id,
        'game_info': game_info,
        'game_moves': game_moves,
        'game_users': game_users,
        'game_size': range(game_info.config_size),
        'title': 'Game room #{}'.format(game_id),
        'url': request.app.router['game_ws'].url(parts={'id': game_id}),
        'user_id': user_id,
        'current_user_in_game': int(current_user_in_game)
    }

async def game_detail_ws(request):
    ''' Game websocket handler '''
    session = await get_session(request)
    user_id = int(session.get('user'))
    game_id = request.match_info['id']

    ws = web.WebSocketResponse()
    await ws.prepare(request)

    for _ws in request.app['websockets']:
        _ws.send_str('%s joined' % user_id)
    request.app['websockets'].append(ws)

    async for msg in ws:
        if msg.tp == MsgType.text:
            if msg.data == 'close':
                await ws.close()
            else:
                data = json.loads(msg.data)

                try:
                    # Check need attributes
                    if 'i' not in data or 'j' not in data:
                        raise Exception('Positions of move are required.')

                    games = Games(request.db)
                    game_users = await games.get_users(game_id)    
                    
                    # Check if user in game
                    if not any(user.id == user_id for user in game_users):
                        raise Exception('You cannot play this game. Create your own to play.')

                    game_info = await games.one(game_id) 

                    # Check if game was not ended
                    if game_info.winner_id:
                        raise Exception('Game is over.')

                    game_moves = await games.get_moves(game_id)

                    check_pairs_moves = (game_info.config_size**2 - len(game_moves) / 2 == 0)
                    check_pairs_user = ((next(index for index, user in enumerate(game_users) if user.id == user_id) + 1) / 2 == 0)

                    # Check if current user must move
                    if check_pairs_user != check_pairs_moves:
                        raise Exception('It is not your turn.')

                    data_moves = [[0]*game_info.config_size for i in range(game_info.config_size)]

                    for moves in game_moves:
                        data_moves[moves.x][moves.y] = moves.users_id                        

                    # Check if the field is available
                    if data_moves[data['i']][data['j']] != 0:
                        raise Exception('This field is not available.')

                    data_moves[data['i']][data['j']] = user_id
                    
                    print('yey!')
                    print(data_moves)

                except Exception as e:
                    print(str(e))

                for _ws in request.app['websockets']:
                    _ws.send_str('(%s) %s' % (user_id, '{}{}'.format(data['i'], data['j'])))
        elif msg.tp == MsgType.error:
            log.debug('ws connection closed with exception %s' % ws.exception())

    request.app['websockets'].remove(ws)
    for _ws in request.app['websockets']:
        _ws.send_str('%s disconected' % user_id)
    log.debug('websocket connection closed')

    return ws