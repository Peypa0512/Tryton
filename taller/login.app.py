import os
from functools import wraps
from flask import Flask, request, render_template,abort, session,redirect,url_for,g
from flask_tryton import Tryton

app = Flask(__name__, static_folder='static', static_url_path="")
app.config['TRYTON_DATABASE'] = os.environ.get('DB_NAME', 'taller_db')
tryton = Tryton(app)

WebUser = tryton.pool('web.user')
UserSession = tryton.pool.get('web.user.session')
#Sale = tryton.pool.get('sale.sale')

def login_required(func):
        @wraps(func)
        def wrapper(*arg, **kwargs):
            session_key = None
            if 'session_key' in session:
                session_key = session['session_key']
            g.user = UserSession.get_user(session_key)
            if not g.user:
                return redirect(url_for('login', next=request.path))
            return func(*arg, **kwargs)
        return wrapper

@app.route('/login', methods=['GET', 'POST'])
@tryton.transaction()
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username and password:
            user = WebUser.authenticate(username, password)
            if user:
                session['session_key'] = WebUser.new_session(user)
                session['username'] = user.email
                if user.party:
                    session['party'] = user.party.id
                next_ = request.form.get('next', None)
                if next_:
                    return redirect(next_)
                redirect('/')
            else:
                return 'Usuario Incorrecto'
    return render_template('login.html')


@app.route('/logout')
@tryton.transaction(readonly=False)
@login_required
def loginout():
    if session['session_key']:
        user_sessions = UserSession.search([('key', '=', session['session_key'])])
        UserSession.delete(user_sessions)
        session.pop('session_key', None)
        session.pop('party', None)
        session.pop('username', None)
    return redirect(request.referrer if request.referrer else url_for('index'))

# @app.route('/my-account')
# @tryton.transaction()
# @login_required
# def myaccount():
#     sales = Sale.search([('party', '=', g.user.party.id)])
#     return render_template('my_account.html', sales=sales)
#
# @app.route('/sale/<record("sale.sale"):sale>')
# @tryton.transaction()
# @login_required
# def sale():
#     if sale.party != g.user.party:
#         return abort(404)