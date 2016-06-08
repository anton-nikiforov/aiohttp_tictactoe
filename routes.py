from game.views import (
	games_create, 
	games_detail, 
	games_join, 
	games_list, 
	game_detail_ws,
    game_replay_ws
	)
from auth.views import login, signin, signout

routes = [
    ('GET', '/', games_list, 'main'),
    ('*', '/game/create', games_create, 'create'),
    ('GET', r'/game/detail/{id:\d+}', games_detail, 'game_detail'),
    ('GET', r'/game/join/{id:\d+}', games_join, 'game_join'),
    ('GET', '/game/ws/{id:\d+}', game_detail_ws, 'game_ws'),
    ('GET', '/game/replay/{id:\d+}', game_replay_ws, 'game_replay'),
    ('*', '/login', login, 'login'),
    ('*', '/signin', signin, 'signin'),
    ('*', '/signout', signout, 'signout'),
]