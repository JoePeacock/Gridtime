import json
import os
import flask

app = flask.Flask(__name__)

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

@app.route('/registerDevice')
def registerDevice():
    resp = dict()
    resp['msg'] = 'win'
    resp['detail'] = 'auth_win'
    device_id = flask.request.args.get('deviceId')
    owner = flask.request.args.get('owner')
    if not device_id or not owner:
        resp['msg'] = 'fail'
        resp['detail'] = 'na'
        return json.dumps(resp)
    d = Device(device_id, owner)
    registered_devices[device_id] = d 
    return json.dumps(resp)

@app.route('/checkIn')
def checkIn():
    resp = dict()
    resp['msg'] = 'win'
    resp['detail'] = 'auth_win'
    device_id = flask.request.args.get('deviceId')
    if not device_id:
        resp['msg'] = 'fail'
        resp['detail'] = 'auth_fail'
        return json.dumps(resp)
    if device_id not in registered_devices:
        resp['msg'] = 'fail'
        resp['detail'] = 'nr'
        return json.dumps(resp)
    return json.dumps(resp)

@app.route('/getJar')
def getDex():
    # Generate Dex file from Jar and then repackage and send over
    task_id = flask.request.args.get('taskId')
    if not task_id:
        return 'Please come back with a taskId next time. Kthx.'
    return task_id


if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

