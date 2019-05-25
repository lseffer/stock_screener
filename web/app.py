from flask import Flask, request, session, redirect
from datetime import timedelta
import os
app = Flask(__name__)
app.secret_key = os.urandom(32)


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
    return redirect('/')


@app.route('/logout', methods=['POST'])
def logout():
    session['logged_in'] = False
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
