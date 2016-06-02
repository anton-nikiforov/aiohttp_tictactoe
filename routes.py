from game.views import games_list, games_create, games_detail, WebSocket
from auth.views import login, signin, signout

routes = [
    ('GET', '/', games_list, 'main'),
    ('*', '/create', games_create, 'create'),
    ('GET', r'/game/{id:\d+}', games_detail, 'game_detail'),
    ('GET', '/ws', WebSocket, 'chat'),
    ('*', '/login', login, 'login'),
    ('*', '/signin', signin, 'signin'),
    ('*', '/signout', signout, 'signout'),
]