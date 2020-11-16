
from flask import Flask, flash, redirect, render_template, request, session, abort, url_for
from functools import wraps

from Main import *
from inst import inst
import timeit

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
    return render_template("4042.html"), 404


@app.route('/coming')
@login_required
def comming_soon():
    return render_template('coming_soon.html')

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
@login_required
def server_info():
    all_instances = []
    start = timeit.default_timer()
    instances_info = get_instances()
    for region, instances in instances_info.items():
        for instance in instances:
            all_instances.append(instance)
    print('all_instances Time: ', timeit.default_timer() - start)
    return render_template('server_details.html', result=all_instances)

@app.route('/server_terminate')
@login_required
def server_terminate():
    terminate_instnace(instance=request.args.get('id'), region=request.args.get('site'))
    all_instances = []
    instances_info = get_instances()
    for region, instances in instances_info.items():
        for instance in instances:
            all_instances.append(instance)
    return render_template('server_details.html', result=all_instances)

@app.route('/server_stop')
@login_required
def server_stop():
    stop_instnace(instance=request.args.get('id'), region=request.args.get('site'))
    all_instances = []
    instances_info = get_instances()
    for region, instances in instances_info.items():
        for instance in instances:
            all_instances.append(instance)
    return render_template('server_details.html', result=all_instances)

@app.route('/server_start')
@login_required
def server_start():
    start_instnace(instance=request.args.get('id'), region=request.args.get('site'))
    all_instances = []
    instances_info = get_instances()
    for region, instances in instances_info.items():
        for instance in instances:
            all_instances.append(instance)
    return render_template('server_details.html', result=all_instances)

@app.route('/AMI_details')
@login_required
def AMI_details():#Take_Time
    start = timeit.default_timer()
    all_images = get_all_images_details('eu-central-1')
    print('all_images Time: ', timeit.default_timer() - start)
    return render_template('images_details.html', result=all_images)

@app.route('/inst', methods=['GET','POST'])
@login_required
def test():
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

@app.route('/start_EC2')
@login_required
def start_EC2():#Take_Time
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

if __name__ == '__main__':
    app.run('0.0.0.0', debug=True)



