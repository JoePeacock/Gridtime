import datetime
from collections import deque
import hashlib
import json
import os
import time

import flask
from werkzeug import secure_filename
import tornado.database

UPLOAD_FOLDER = 'upload'
ALLOWED_EXTENSIONS = set(['java', 'txt'])

app = flask.Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.debug = True

db = tornado.database.Connection("localhost", "gridtime", "root", "gtroot")

def getRegisteredDevices():
    rd = dict()
    devices = db.query('select * from devices')
    for d in devices:
        rd[str(d['id'])] = d
    return rd

def getAllTasks():
    rt = dict()
    tasks = db.query('select * from tasks')
    for t in tasks:
        rt[str(t['id'])] = t
    return rt

registered_devices = getRegisteredDevices() # {device_id: Device, ...}
waiting_devices = dict() # {device_id: Device, ...}
working_devices = dict() # {device_id: Device, ...}

all_tasks = getAllTasks()
incomplete_tasks = deque() # {task_id: Task, ...}
running_tasks = deque() # {task_id: Task, ...}

@app.route('/')
def hello():
    return flask.render_template('index.html')

@app.route('/registerDevice', methods=['POST'])
def registerDevice():
    resp = dict()
    resp['msg'] = 'win'
    resp['detail'] = 'auth_win'
    data = dict(flask.request.json)
    if not data:
        resp['msg'] = 'fail'
        resp['detail'] = 'no_data'
        return json.dumps(resp)
    if 'deviceId' not in data or 'ownerId' not in data:
        resp['msg'] = 'fail'
        resp['detail'] = 'malformed_input'
        return json.dumps(resp)
    device_id = data['deviceId']
    owner = data['ownerId']
    d = db.get('select * from devices where id = %s and owner_email = %s', device_id, owner)
    if d:
        resp['msg'] = 'fail'
        resp['detail'] = 'already_registered'
        return json.dumps(resp)
    else:
        t = datetime.datetime.now()
        db.execute('insert into devices (id, owner_email, task_id, last_checkin) values (%s, %s, -1, %s)', device_id, owner, t)
    d = db.get('select * from devices where id = %s and owner_email = %s', device_id, owner)
    if d['id'] not in registered_devices:
        registered_devices[device_id] = d
    return json.dumps(resp)

def distributeTask(device_id):
    if running_tasks:
        return running_tasks[len(running_tasks) - 1]
    return -1

@app.route('/checkIn', methods=['POST'])
def checkIn():
    resp = dict()
    data = dict(flask.request.json)
    if 'deviceId' not in data or 'state' not in data:
        resp['msg'] = 'fail'
        resp['detail'] = 'malformed_input'
        return json.dumps(resp)
    device_id = data['deviceId']
    state = data['state']
    if device_id not in registered_devices:
        resp['msg'] = 'fail'
        resp['detail'] = 'not_registered'
        return json.dumps(resp)
    t = datetime.datetime.now()
    db.execute('update devices set last_checkin=%s where id=%s', t, device_id)
    if state == 'waiting':
        if device_id not in waiting_devices:
            waiting_devices[device_id] = registered_devices[device_id]
        task_id = distributeTask(device_id) 
        # If no tasks available
        if task_id == -1:
            resp['msg'] = 'fail'
            resp['detail'] = 'no_avail_tasks'
            return json.dumps(resp)
        resp['msg'] = 'win'
        resp['detail'] = 'new_task'
        resp['task_id'] = task_id
        db.execute('update devices set task_id = %s where id = %s', task_id, device_id)
        return json.dumps(resp)
    elif state == 'working':
        if device_id not in working_devices:
            working_devices[device_id] = registered_devices[device_id]
        resp['msg'] = 'win'
        resp['detail'] = 'auth_win'
        return json.dumps(resp)
    return json.dumps(resp)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/createTask', methods=['POST'])
def createTask():
    resp = dict()
    resp['msg'] = 'win'
    resp['detail'] = 'task_win'
    owner_id = flask.request.form['ownerId']
    total_nodes_wanted = int(flask.request.form['totalNodesWanted'])
    code = flask.request.files['deviceCode']
    data_file = flask.request.files['dataFile']
    if not owner_id or not server_code or not device_code:
        resp['msg'] = 'fail'
        resp['details'] = 'malformed_input'
        return json.dumps(resp)
    if not allowed_file(server_code) and not allowed_file(device_code) and not allowed_file(data_file):
        resp['msg'] = 'fail'
        resp['details'] = 'bad_file'
        return json.dumps(resp)

    code_name = secure_filename(code.filename)
    data_file_name = secure_filename(data_file.filename)
    code.save(os.path.join(app.config['UPLOAD_FOLDER'], code_name))
    data_file.save(os.path.join(app.config['UPLOAD_FOLDER'], data_file_name))
    last_id = db.execute('insert into tasks (owner_email, wanted_devices, dex_path, server_bin_path, data_file_path, name) values (%s, %s, %s, %s, %s, %s)',
            owner_id, total_nodes_wanted, device_code_name, server_code_name, data_file_name, task_id)
    t = db.get('select * from tasks where id = %s', last_id)
    all_tasks[t.task_id] = t
    running_tasks.appendleft(t.task_id)

    #create the jar'd dex
    os.system("mv " + device_code_name + " /home/ubuntu/runner/src/gridtime/Test.java")
    os.system("cd /home/ubuntu/runner/;ant;ant release")
    os.system("mkdir /home/ubuntu/task_jars/" + str(t['id']))
    os.system("jar -cf /home/ubuntu/task_jars/" + str(t['id']) + "/Test.jar /home/ubuntu/runner/bin/classes.dex")

    return flask.redirect(flask.url_for('taskStatus'))

@app.route('/getTask')
def getTask():
    data = dict(flask.request.json)
    if not data:
        return str(-3)
    if 'deviceId' not in data or 'taskId' not in data:
        return str(-3)
    device_id = data['deviceId']
    if device_id not in registered_devices:
        return str(-1)
    task_id = data['taskId']
    if task_id not in running_tasks:
        return str(-2)

    return flask.send_file("/home/ubuntu/task_jars/" + str(data['taskId'] + "/Test.jar")) # Generate Dex file from Jar and then repackage and send over

@app.route('/submitResult', methods=['POST'])
def submitResult():
    resp = dict()
    resp['msg'] = 'win'
    resp['detail'] = 'submit_win'
    data = dict(flask.request.json)
    if not data or 'deviceId' not in data or 'result' not in data:
        resp['msg'] = 'fail'
        resp['detail'] = 'malformed_submit'
        return json.dumps(resp)
    device_id = data['deviceId']
    result = data['result']
    d = db.get('select * from devices where id = %s')
    task_id = d.task_id
    result_count = db.get('select count(id) from results where task_id = %s', task_id)['count(id)']
    devices_wanted = db.get('select * from tasks where id = %s', task_id)['wanted_devices']
    if result_count == devices_wanted:
        resp['msg'] = 'fail'
        resp['detail'] = 'task_done'
        if os.path.exists("/home/ubuntu/task_jars/" + str(task_id) + "/"):
            os.system("rm -r /home/ubuntu/task_jars/" + str(task_id) + "/")
        return json.dumps(resp)
    else:
        db.execute('insert into results (value_type, value, task_id, device_id) values (%s, %s, %s, %s)', 'String', result, task_id, device_id)
        del working_devices[device_id]
        db.execute('update devices set task_id = %s where device_id = %s', -1, device_id)
        waiting_devices[device_id] = registered_devices[device_id]
        return json.dumps(resp)
   

@app.route('/taskStatus')
def taskStatus():
    return flask.redirect(flask.url_for('debug'))

@app.route('/login', methods=['GET','POST'])
def login():
    if flask.request.method == 'POST':
        return flask.redirect(flask.url_for('admin'))
    else:
        return flask.render_template('login.html')

@app.route('/admin')
def admin():
    return flask.render_template('admin.html', registered_devices = registered_devices.values(), waiting_devices = waiting_devices.values(), running_tasks = running_tasks)

@app.route('/about')
def about():
    return flask.render_template('resabout.html')

@app.route('/signUp')
def signUp():
    return flask.render_template('signup.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10080)


