from flask import Flask, flash, redirect, render_template, request, session, abort, url_for
from functools import wraps
from time import sleep

app = Flask(__name__)

# config
app.secret_key = 'my precious'

session = {}

# login required decorator
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('You need to login first.')
            return redirect(url_for('login'))
    return wrap

@app.route('/')
@login_required
def index():
    return redirect(url_for('login'))

# route for handling the login page logic
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != 'admin' or request.form['password'] != 'admin':
            error = 'Invalid Credentials. Please try again.'
        else:
            session['logged_in'] = True
            flash('You were logged in.')
            return render_template('Main.html', error=error)
    return render_template('login.html', error=error)

# app name
@app.errorhandler(404)
@login_required
def not_found(e):
    # abort(404)
    return render_template("4042.html"), 404


@app.route('/coming')
@login_required
def comming_soon():
    sleep(10)
    return render_template('coming_soon.html')

@app.route('/bill')
def bill():
    sleep(10)
    return render_template('coming_soon.html')

@app.route('/server_count')
def server_count():
    sleep(10)
    return render_template('coming_soon.html')

@app.route('/server_info')
@login_required
def server_info():
    sleep(10)
    return render_template('coming_soon.html')

@app.route('/server_terminate')
@login_required
def server_terminate():
    sleep(10)
    return render_template('coming_soon.html')

@app.route('/server_stop')
@login_required
def server_stop():
    sleep(10)
    return render_template('coming_soon.html')

@app.route('/server_start')
@login_required
def server_start():
    sleep(10)
    return render_template('coming_soon.html')

@app.route('/AMI_details')
@login_required
def AMI_details():#Take_Time
    sleep(10)
    return render_template('coming_soon.html')

@app.route('/inst', methods=['GET', 'POST'])
@login_required
def test():
    sleep(10)
    return render_template('coming_soon.html')

@app.route('/start_EC2')
@login_required
def start_EC2():#Take_Time
    sleep(10)
    return render_template('coming_soon.html')

if __name__ == '__main__':
    app.run('0.0.0.0',debug=True)