from flask import Flask, request, session, flash
import os
app = Flask(__name__)
app.secret_key = os.urandom(32)


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
    else:
        flash('Wrong login credentials!')
    return index()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
