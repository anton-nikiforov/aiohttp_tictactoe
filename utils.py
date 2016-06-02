from aiohttp import web

def redirect(request, router_name):
    url = request.app.router[router_name].url()
    raise web.HTTPFound(url)