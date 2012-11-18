import hashlib
import json
import os
import time

import flask
from werkzeug import secure_filename

UPLOAD_FOLDER = 'upload'
ALLOWED_EXTENSIONS = set(['java', 'txt'])

app = flask.Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.debug = True

registered_devices = dict() # {device_id: Device, ...}
waiting_devices = dict() # {device_id: Device, ...}
all_tasks = dict() # {task_id: Task, ...}
running_tasks = dict() # {task_id: Task, ...}

class Device(object):
    def __init__(self, d, o): 
        self.device_id = d 
        self.owner = o 
        self.current_task_id = None
        self.last_checkin = int(time.time())

class Task(object):
    def __init__(self, o, t, n, ptd, ptsb, dfn):
        self.owner = o
        self.task_id = t
        self.active_nodes = list() # [device_id, device_id, ...]
        self.total_nodes_wanted = n
        self.path_to_dex = ptd
        self.path_to_server_binary = ptsb
        self.path_to_data_file = dfn

@app.route('/debug')
def debug():
    s = "<html><body><h2>Registered Devices</h2>"
    if not registered_devices:
        s += '<p>No registered devices.</p>'
    else:
        s += '<p>DeviceId Owner TaskId LastCheckin</p>'
        for device in registered_devices:
            device = registered_devices[device]
            s += ('<p>' + str(device.device_id) + ' ' + str(device.owner) + ' ' + str(device.current_task_id) + ' ' + str(device.last_checkin) + '</p>')
    s += '<h2>Waiting Devices</h2>'
    if not waiting_devices:
        s += '<p>No waiting devices.</p>'
    else:
        s += '<p>DeviceId Owner TaskId LastCheckin</p>'
        for device in waiting_devices:
            device = registered_devices[device]
            s += ('<p>' + str(device.device_id) + ' ' + str(device.owner) + ' ' + str(device.current_task_id) + ' ' + str(device.last_checkin) + '</p>')
    s += '<h2>Running Tasks</h2>'
    if not running_tasks:
        s += '<p>No Tasks.</p>'
    else:
        s += '<p>TaskId ActiveNodes TotalNodesWanted PathToDex PathToServerBinary</p>'
        for task in running_taks:
            task =  all_tasks[task]
            s += ('<p>' + str(task.task_id) + ' [')
            for device_id in task.active_nodes:
                s += device_id + ', '
            s += '] ' + task.total_nodes_wanted + ' ' + task.path_to_dex + ' ' + task.path_to_server_binary + '</p>'
    s += '</body></html>'
    return s

@app.route('/')
def hello():
    return 'We\'re GridTime. Charge your phone, charge your wallet.'

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
    if 'deviceId' not in data or 'owner' not in data:
        resp['msg'] = 'fail'
        resp['detail'] = 'malformed_input'
        return json.dumps(resp)
    device_id = data['deviceId']
    owner = data['owner']
    d = Device(device_id, owner)
    if d.device_id not in registered_devices:
        registered_devices[device_id] = d
    else:
        resp['msg'] = 'fail'
        resp['detail'] = 'already_registered'
        return json.dumps(resp)
    if d.device_id not in waiting_devices:
        waiting_devices[d.device_id] = d
    else:
        resp['msg'] = 'fail'
        resp['detail'] = 'already_waiting'
        return json.dumps(resp)
    return json.dumps(resp)

def distributeTask(device_id):
    return device_id

@app.route('/checkIn', methods=['POST'])
def checkIn():
    resp = dict()
    resp['msg'] = 'win'
    resp['detail'] = 'auth_win'
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
    if state is 'waiting':
        task_id = distributeTask(device_id) # distributes the next queued task to the device and returns the task id
        resp['msg'] = 'win'
        resp['detail'] = 'new_task'
        resp['task_id'] = task_id
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
    server_code = flask.request.files['serverCode']
    device_code = flask.request.files['deviceCode']
    data_file = flask.request.files['dataFile']
    if not owner_id or not server_code or not device_code:
        resp['msg'] = 'fail'
        resp['details'] = 'malformed_input'
        return json.dumps(resp)
    if not allowed_file(server_code) and not allowed_file(device_code) and not allowed_file(data_file):
        resp['msg'] = 'fail'
        resp['details'] = 'bad_file'
        return json.dumps(resp)
    server_code_name = secure_filename(server_code.filename)
    device_code_name = secure_filename(device_code.filename)
    data_file_name = secure_filename(data_file.filename)
    server_code.save(os.path.join(app.config['UPLOAD_FOLDER'], server_code_name))
    device_code.save(os.path.join(app.config['UPLOAD_FOLDER'], device_code_name))
    data_file.save(os.path.join(app.config['UPLOAD_FOLDER'], data_file_name))
    t = Task(owner_id, hashlib.sha256(owner_id + time.time()).hexdigest(), total_nodes_wanted,
            device_code_name, server_code_name, data_file_name)
    all_tasks[t.task_id] = t
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
    return task_id # Generate Dex file from Jar and then repackage and send over

@app.route('/taskStatus')
def taskStatus():
    return 'hi'    

@app.route('/login', methods=['POST'])
def login():
    resp = dict()
    resp['msg'] = 'win'
    resp['detail'] = 'auth_win'
    data = dict(flask.request.json)
    if 'username' not in data or 'password' not in data:
        resp['msg'] = 'fail'
        resp['detail'] = 'auth_fail'
        return json.dumps(resp)
    username = data['username']
    password = data['password']
    if not username or not password:
        resp['msg'] = 'fail'
        resp['detail'] = 'auth_fail'
        return json.dumps(resp)
    return json.dumps(resp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10080)


