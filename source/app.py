import os
import base64
from io import BytesIO


import pyqrcode
import onetimepass
from flask_wtf import FlaskForm
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from wtforms.validators import Required, Length, EqualTo
from wtforms import StringField, PasswordField, SubmitField,BooleanField
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from flask import Flask, render_template, redirect, url_for, flash, session, abort , flash, request, Response, send_file
from functools import wraps

from Main import *
from inst import inst
import timeit


# config
app = Flask(__name__)

app.config.from_object('config')

# initialize extensions
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
lm = LoginManager(app)


def remove_password(username):
    User.query.filter_by(username=username).delete()
    db.session.commit()

def change_password(username, password, adminb):
    admin = User.query.filter_by(username=username).first()
    admin.password = password
    admin.admin = adminb
    db.session.commit()

class User(UserMixin, db.Model):
    """User model."""
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True)
    password_hash = db.Column(db.String(128))
    otp_secret = db.Column(db.String(16))
    admin = db.Column(db.Boolean())

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.otp_secret is None:
            # generate a random secret
            self.otp_secret = base64.b32encode(os.urandom(10)).decode('utf-8')

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_totp_uri(self):
        return f'otpauth://totp/AWSforDummies:{self.username}?secret={self.otp_secret}&issuer=AWSforDummies'

    def verify_totp(self, token):
        return onetimepass.valid_totp(token, self.otp_secret)


@lm.user_loader
def load_user(user_id):
    """User loader callback for Flask-Login."""
    return User.query.get(int(user_id))


class AddUserForm(FlaskForm):
    """Add User Form."""
    username = StringField('Username', validators=[Required(), Length(1, 64)])
    password = PasswordField('Password', validators=[Required(), Length(8, 8)])
    password_again = PasswordField('Password again', validators=[Required(), EqualTo('password', message='Passwords must match')])
    admin = BooleanField('Admin')
    submit = SubmitField('Add')


class ChangePasswordForm(FlaskForm):
    """Change Password Form."""
    username = StringField('Username', validators=[Required(), Length(1, 64)])
    password = PasswordField('Password', validators=[Length(8, 8)])
    password_again = PasswordField('Password again', validators=[EqualTo('password', message='Passwords must match')])
    admin = BooleanField('Admin')
    Remove = BooleanField('Remove')
    submit = SubmitField('Change')

class LoginForm(FlaskForm):
    """Login form."""
    username = StringField('Username', validators=[Required(), Length(1, 64)])
    password = PasswordField('Password', validators=[Required(), Length(8, 8)])
    token = StringField('Token', validators=[Required(), Length(6, 6)])
    submit = SubmitField('Login')


@app.errorhandler(404)
def error404(error):
    if current_user.is_authenticated:
        return render_template("404.html"), 404
    return redirect(url_for('login'))

@app.errorhandler(500)
def error500(error):
    number = 50
    msg1 = 'Oops! Server Error!'
    msg2 = 'Uh ohhhh! Somersoult jump!.'
    return render_template("error_page.html", number=number, msg1=msg1, msg2=msg2), 500

@app.errorhandler(405)
def error405(error):
    number = 45
    msg1 = 'Oops! Method Not Allowed!'
    msg2 = 'AIDS!'
    return render_template("error_page.html", number=number, msg1=msg1, msg2=msg2), 405

@app.errorhandler(403)
def error403(error):
    number = 43
    msg1 = 'Forbidden!'
    msg2 = "Hey, I'M SQUANCHING HERE!, GO AWAY!"
    return render_template("error_page.html", number=number, msg1=msg1, msg2=msg2), 403

@app.errorhandler(401)
def error401(error):
    number = 41
    msg1 = 'Unauthorized!'
    msg2 = "And that's why I always say, 'Shumshumschilpiddydah!"
    return render_template("error_page.html", number=number, msg1=msg1, msg2=msg2), 401


@app.route('/')
def index():
    if current_user.is_authenticated:
        return render_template("Main.html")
    return redirect(url_for('login'))


@app.route('/adduser', methods=['GET', 'POST'])
def adduser():

    try:
        print(current_user.admin)
        if User.query.filter_by(username=current_user.username, admin=True).first():
            admin = True
        else:
            admin = False
        login_state = True
    except:
        admin = False
        login_state = False
    if current_user.is_authenticated and admin or len(User.query.limit(10).all()) == 0:
        form = AddUserForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user is not None:
                flash('Username already exists.')
                return redirect(url_for('register'))
            # add new user to the database
            user = User(username=form.username.data, password=form.password.data, admin=form.admin.data)
            db.session.add(user)
            db.session.commit()

            # redirect to the two-factor auth page, passing username in session
            session['username'] = user.username
            return redirect(url_for('two_factor_setup'))
        return render_template('adduser.html', form=form)
    if login_state == False:
        return redirect(url_for('login'))
    else:
        flash('Not Admin user. Please contact the administrative user.')
        return redirect(url_for('index'))

@app.route('/passwordchange', methods=['GET', 'POST'])
def passwordchange():

    try:
        if User.query.filter_by(username=current_user.username, admin=True).first():
            admin = True
        else:
            admin = False
        login_state = True
    except:
        admin = False
        login_state = False

    if current_user.is_authenticated and admin:
        form = ChangePasswordForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user is None:
                flash('User Dose\'t exists.')
                return redirect(url_for('passwordchange'))
            # change new user to the database
            if not form.remove.data:
                change_password(username=form.username.data, password=form.password.data, adminb=form.admin.data)
            else:
                remove_user(username=form.username.data)
            flash('User Details Change Successfully.')
        return render_template('passwordchange.html', form=form)
    if login_state == False:
        return redirect(url_for('login'))
    else:
        flash('Not Admin user. Please contact the administrative user.')
        return redirect(url_for('index'))


@app.route('/twofactor')
def two_factor_setup(): #todo: first validation
    if 'username' not in session:
        return redirect(url_for('index'))
    user = User.query.filter_by(username=session['username']).first()
    if user is None:
        return redirect(url_for('index'))
    # since this page contains the sensitive qrcode, make sure the browser
    # does not cache it
    return render_template('two-factor-setup.html'), 200, {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'}


@app.route('/qrcode')
def qrcode():

    if 'username' not in session:
        abort(404)
    user = User.query.filter_by(username=session['username']).first()
    if user is None:
        abort(404)

    # for added security, remove username from session
    del session['username']

    # render qrcode for FreeTOTP
    url = pyqrcode.create(user.get_totp_uri())
    stream = BytesIO()
    url.svg(stream, scale=3)
    return stream.getvalue(), 200, {
        'Content-Type': 'image/svg+xml',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'}


@app.route('/login', methods=['GET', 'POST'])
def login():
    count_users = len(User.query.limit(10).all())
    """User login route."""
    if current_user.is_authenticated:
        # if user is logged in we get out of here
        return redirect(url_for('login'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.verify_password(form.password.data) or \
                not user.verify_totp(form.token.data):
            flash('Invalid username, password or token.')
            return redirect(url_for('login'))
        # log user in
        login_user(user)
        # flash('You are now logged in!')
        return redirect(url_for('index'))
    return render_template('login.html', form=form,ucount = count_users)


@app.route('/logout')
def logout():

    """User logout route."""
    logout_user()
    session.clear()
    return redirect(url_for('index'))


@app.route('/coming')
def comming_soon():
    if current_user.is_authenticated:
        return render_template('coming_soon.html')
    return redirect(url_for('login'))

@app.route('/bill')
def bill(): #todo:c
    start = timeit.default_timer()
    tup_res = run_func_in_threads_pool(func=get_bill_by_month, args_lists=[[True], [False]])
    currentdate, currentbill = tup_res[0]
    lastdate, lastbill = tup_res[1]
    print('bill Time: ', timeit.default_timer() - start)
    return render_template('bill.html', currentdate=currentdate, currentbill=currentbill, lastdate=lastdate, lastbill=lastbill)

@app.route('/server_count')
def server_count():
    start = timeit.default_timer()
    instances = count_instances()
    print('all_instances Time: ', timeit.default_timer() - start)
    return render_template('server_count.html', result=instances)

@app.route('/server_info')
def server_info():
    if current_user.is_authenticated:
        all_instances = []
        start = timeit.default_timer()
        instances_info = get_instances()
        for region, instances in instances_info.items():
            for instance in instances:
                all_instances.append(instance)
        print('all_instances Time: ', timeit.default_timer() - start)
        return render_template('server_details.html', result=all_instances)
    return redirect(url_for('login'))

@app.route('/server_terminate')
def server_terminate():
    if current_user.is_authenticated:
        terminate_instnace(instance=request.args.get('id'), region=request.args.get('site'))
        all_instances = []
        instances_info = get_instances()
        for region, instances in instances_info.items():
            for instance in instances:
                all_instances.append(instance)
        return render_template('server_details.html', result=all_instances)
    return redirect(url_for('login'))

@app.route('/server_stop')
def server_stop():
    if current_user.is_authenticated:
        stop_instnace(instance=request.args.get('id'), region=request.args.get('site'))
        all_instances = []
        instances_info = get_instances()
        for region, instances in instances_info.items():
            for instance in instances:
                all_instances.append(instance)
        return render_template('server_details.html', result=all_instances)
    return redirect(url_for('login'))

@app.route('/server_start')
def server_start():
    if current_user.is_authenticated:
        start_instnace(instance=request.args.get('id'), region=request.args.get('site'))
        all_instances = []
        instances_info = get_instances()
        for region, instances in instances_info.items():
            for instance in instances:
                all_instances.append(instance)
        return render_template('server_details.html', result=all_instances)
    return redirect(url_for('login'))

@app.route('/AMI_details')
def AMI_details():#Take_Time
    if current_user.is_authenticated:
        start = timeit.default_timer()
        all_images = get_all_images_details('eu-central-1')
        print('all_images Time: ', timeit.default_timer() - start)
        return render_template('images_details.html', result=all_images)
    return redirect(url_for('login'))

@app.route('/inst', methods=['GET','POST'])
def test():
    if current_user.is_authenticated:
        if request.method == 'POST':
            KeyPair = request.form['KeyPair'].strip()
            # Bucket = request.form['Bucket']
            Production = request.form['Production'].strip()
            MachineName = request.form['MachineName'].strip()
            InstanceProfiles = request.form['InstanceProfiles'].strip()
            SecurityGroups = request.form['SecurityGroups'].strip()
            EC2Types = request.form['EC2Types'].strip()
            Site = request.form['Site'].strip()
            InstanceID = request.form['InstanceID'].strip()
            Spot = request.form['Spot'].strip()
            inst(verbose=False, spot=Spot, key=KeyPair, region=Site, ami=InstanceID, instancetype=EC2Types, SecurityGroup=SecurityGroups, IamInstanceProfile=InstanceProfiles, name=MachineName, prod=Production)
            all_instances = []
            start = timeit.default_timer()
            instances_info = get_instances()
            for region, instances in instances_info.items():
                for instance in instances:
                    all_instances.append(instance)
            print('all_instances Time: ', timeit.default_timer() - start)
            return render_template('server_details.html', result=all_instances)
    return redirect(url_for('login'))

@app.route('/start_EC2')
def start_EC2():#Take_Time
    if current_user.is_authenticated:
        start = timeit.default_timer()
        buckets = get_s3_bucket_names(request.args.get('site'))
        print('buckets Time: ', timeit.default_timer() - start)

        start = timeit.default_timer()
        instance_profiles = get_instance_profiles_names(request.args.get('site'))
        print('instance_profiles Time: ', timeit.default_timer() - start)

        start = timeit.default_timer()
        security_groups = get_all_SG(request.args.get('site'))
        print('security_groups Time: ', timeit.default_timer() - start)

        start = timeit.default_timer()
        keypairs = get_keypairs_details(request.args.get('site'))
        print('keypairs Time: ', timeit.default_timer() - start)

        start = timeit.default_timer()
        if 'Linux' in request.args.get('os'):
            os = 'linux'
        else:
            os = 'windows'
        EC2_types = get_all_EC2_types(os, request.args.get('site'), all=False)  # Take_Time if all = True (false in progress)
        print('EC2_types Time: ', timeit.default_timer() - start)
        return render_template('Start_EC2.html', site=request.args.get('site'), spot=request.args.get('spot'), instanceid=request.args.get('id'), keypairs=keypairs, buckets=buckets, instance_profiles=instance_profiles,
                               security_groups=security_groups, EC2_types=EC2_types)
    return redirect(url_for('login'))
db.create_all()

if __name__ == '__main__':
    app.run('0.0.0.0', debug=True)



