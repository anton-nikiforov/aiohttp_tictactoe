import json

import aiohttp_jinja2
from aiohttp_session import get_session
from aiohttp import web, MsgType

from auth.models import User
from game.forms import GameCreateForm
from game.models import Games
from settings import log, PLAYERS_IN_GAME, STATUS, DRAW
from utils import redirect, check_for_winner

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
        if not one.finished and one.users_count < PLAYERS_IN_GAME and \
                user_id not in list(map(int, one.users_ids.split(','))):
            data_one['url'] = request.app.router['game_join'].url(parts={'id': one.id})
            data_one['url_label'] = 'Join'
        else:
            data_one['url'] = request.app.router['game_detail'].url(parts={'id': one.id})
            data_one['url_label'] = 'View'  
        if one.finished and one.winner_id == DRAW:
            data_one['winner_login'] = 'Draw'
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

    size = game_info.config_size

    data_moves = [[0]*size for i in range(size)]

    for moves in game_moves:
        data_moves[moves.x][moves.y] = str(moves.users_id)  

    current_user_in_game = any(user.id == user_id for user in game_users)
    next_user_id = game_users[int((size**2 - len(game_moves)) % 2 == 0)].id

    return {
        'game_id': game_id,
        'game_info': game_info,
        'data_moves': data_moves,
        'game_users': game_users,
        'game_size': range(size),
        'title': 'Game room #{}'.format(game_id),
        'url': request.app.router['game_ws'].url(parts={'id': game_id}),
        'user_id': user_id,
        'current_user_in_game': int(current_user_in_game),
        'next_user_id': next_user_id,
        'response_status': json.dumps(STATUS)
    }

async def game_detail_ws(request):
    ''' Game websocket handler '''
    session = await get_session(request)
    user_id = int(session.get('user'))
    game_id = request.match_info['id']

    ws = web.WebSocketResponse(autoclose=False)
    await ws.prepare(request)

    opened_ws = request.app['websockets'][game_id]

    for _ws in opened_ws:
        _ws.send_str(json.dumps({'message': '{} joined'.format(user_id), 'status': STATUS['INFO']}))
    opened_ws.append(ws)

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
                        raise Exception('You cannot play this game. Create your own to game.')

                    game_info = await games.one(game_id) 

                    # Check if game was not ended
                    if game_info.winner_id:
                        raise Exception('Game is over.')

                    game_moves = await games.get_moves(game_id)

                    check_pairs_moves = ((game_info.config_size**2 - len(game_moves)) % 2 == 0)
                    check_pairs_user = ((next(index for index, user in enumerate(game_users) if user.id == user_id) + 1) % 2 == 0)

                    # Check if current user must move
                    if check_pairs_user != check_pairs_moves:
                        raise Exception('It is not your turn.')

                    data_moves = [[0]*game_info.config_size for i in range(game_info.config_size)]

                    for moves in game_moves:
                        data_moves[moves.x][moves.y] = str(moves.users_id)                        

                    # Check if the field is available
                    if data_moves[data['i']][data['j']]:
                        raise Exception('This field is not available.')

                    data_moves[data['i']][data['j']] = str(user_id)
                    
                    # Save move
                    await games.save_move(user_id, game_id, data['i'], data['j'])

                    # Check game for winner
                    winner_id = await check_for_winner(data_moves)

                    # Draw
                    if game_info.config_size**2 == (len(game_moves) + 1) and not winner_id:
                        winner_id = DRAW

                    # if we find winner -> game is end.
                    if winner_id:
                        await games.finish_game(game_id, winner_id)

                    context = {
                        'status': STATUS['OK'],
                        'winner_id': winner_id,
                        'next_user_id': next(user.id for user in game_users if user.id != user_id),
                        'current_user_id': user_id,
                        'i': data['i'],
                        'j': data['j'],
                        'message': '{} made choice'.format(user_id)
                    }

                except Exception as e:
                    print(str(e))
                    context = {
                        'status': STATUS['ERROR'],
                        'message': str(e)
                    }

                for _ws in opened_ws:
                    _ws.send_str(json.dumps(context))
        elif msg.tp == MsgType.error:
            log.debug('ws connection closed with exception {}'.format(ws.exception()))

    opened_ws.remove(ws)
    for _ws in opened_ws:
        _ws.send_str(json.dumps({'message': '{} disconected'.format(user_id), 'status': STATUS['INFO']}))
    log.debug('websocket connection closed')

    return ws