import json
import os
import flask

app = flask.Flask(__name__)
app.debug = True

registered_devices = dict()
waiting_devices = dict()
running_devices = dict()

class Device(object):
    def __init__(self, d, o): 
        self.device_id = d 
        self.owner = o 
        self.current_task_id = None

@app.route('/')
def hello():
    return 'We\'re GridTime. Charge your phone, charge your wallet.'

@app.route('/registerDevice', methods=['POST'])
def registerDevice():
    resp = dict()
    resp['msg'] = 'win'
    resp['detail'] = 'auth_win'
    device_id = flask.request.args.get('deviceId')
    owner = flask.request.args.get('owner')
    if not device_id or not owner:
        resp['msg'] = 'fail'
        resp['detail'] = 'malformed_input'
        return json.dumps(resp)
    d = Device(device_id, owner)
    if d.device_id not in registered_devices:
        registered_devices[device_id] = d 
    return json.dumps(resp)

@app.route('/checkIn', methods=['POST'])
def checkIn():
    resp = dict()
    resp['msg'] = 'win'
    resp['detail'] = 'auth_win'
    data = dict(flask.request.json)
    if 'deviceId' not in data:
        resp['msg'] = 'fail'
        resp['detail'] = 'malformed_input'
        return json.dumps(resp)
    device_id = data['deviceId']
    if not device_id:
        resp['msg'] = 'fail'
        resp['detail'] = 'auth_fail'
        return json.dumps(resp)
    if device_id not in registered_devices:
        resp['msg'] = 'fail'
        resp['detail'] = 'not_registered'
        return json.dumps(resp)
    return json.dumps(resp)

@app.route('/getJar')
def getDex():
    # Generate Dex file from Jar and then repackage and send over
    task_id = flask.request.args.get('taskId')
    if not task_id:
        return 'Please come back with a taskId next time. Kthx.'
    return task_id

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


