from flask import Flask, request, session, redirect, abort, url_for
from flask_jsontools import jsonapi
from datetime import timedelta
from utils.queries import screened_stocks
from utils import ApiJSONEncoder
import os


class ReverseProxied(object):
    '''Wrap the application in this middleware and configure the
    front-end server to add these headers, to let you quietly bind
    this to a URL other than / and to an HTTP scheme that is
    different than what is used locally.

    In nginx:
    location /myprefix {
        proxy_pass http://192.168.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Scheme $scheme;
        proxy_set_header X-Script-Name /myprefix;
        }

    :param app: the WSGI application
    '''

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        script_name = environ.get('HTTP_X_SCRIPT_NAME', '')
        if script_name:
            environ['SCRIPT_NAME'] = script_name
            path_info = environ['PATH_INFO']
            if path_info.startswith(script_name):
                environ['PATH_INFO'] = path_info[len(script_name):]

        scheme = environ.get('HTTP_X_SCHEME', '')
        if scheme:
            environ['wsgi.url_scheme'] = scheme
        return self.app(environ, start_response)


app = Flask(__name__)
app.secret_key = os.getenv('SESSION_SECRET')
app.json_encoder = ApiJSONEncoder
app.wsgi_app = ReverseProxied(app.wsgi_app)


@app.route("/stocks", methods=["GET"])
@jsonapi
def stocks():
    if session.get('logged_in'):
        result = screened_stocks()
        return result
    else:
        return abort(401)


@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=60)


@app.route('/')
def index():
    if session.get('logged_in'):
        return app.send_static_file('index.html')
    else:
        return app.send_static_file('login.html')


@app.route('/login', methods=['POST'])
def login():
    if request.form.get('password') == os.getenv('STOCKS_PASSWORD') and \
            request.form.get('username') == os.getenv('STOCKS_USERNAME'):
        session['logged_in'] = True
    return redirect(url_for('.index', _external=True))


@app.route('/logout', methods=['POST'])
def logout():
    session['logged_in'] = False
    return redirect(url_for('.index', _external=True))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
