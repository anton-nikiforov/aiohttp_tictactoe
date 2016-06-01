from time import time

import aiohttp_jinja2
from aiohttp_session import get_session
from aiohttp import web

from auth.models import User
from auth.forms import SignInForm, LoginForm
from utils import redirect

def set_session(session, user_id, request):
    session['user'] = str(user_id)
    session['last_visit'] = time()
    print(session)
    redirect(request, 'main')

@aiohttp_jinja2.template('auth/login.html')
async def login(request):
    session = await get_session(request)
    if session.get('user'):
        redirect(request, 'main')

    form = LoginForm()
    if request.method == 'POST':
        form.process(await request.post())
        if form.validate():
            user = User(request.db)
            result = await user.authenticate(email=form.email.data, password=form.password.data)       
            if result.rowcount:
                row = await result.fetchone()
                session = await get_session(request)
                set_session(session, row['id'], request)
                redirect(request, 'main')
    return {'title': 'Please enter login or email', 'form': form} 

@aiohttp_jinja2.template('auth/sign.html')
async def signin(request):
    session = await get_session(request)
    if session.get('user'):
        redirect(request, 'main')

    form = SignInForm()
    if request.method == 'POST':
        form.process(await request.post())
        if form.validate():
            user = User(request.db)
            check = await user.check_email(form.email.data)
            if check.rowcount:
                redirect(request, 'login')
            result = await user.save(form.data)
            if result.lastrowid:
                session = await get_session(request)
                set_session(session, result.lastrowid, request)
                redirect(request, 'login')
    return {'title': 'Please sign in', 'form': form}

async def signout(request):
    session = await get_session(request)
    if session.get('user'):
        del session['user']
        redirect(request, 'login')
    else:
        raise web.HTTPForbidden(body=b'Forbidden')
