import os
from dotenv import load_dotenv
load_dotenv()

import requests
from users import host, join, roundResult, remove, freeRoamResult, freeRoamSurvey, allResults
from session import sessionStatus, advanceSession, roundResults, finalResults, surveysSubmitted, playersInSession, endSession
from simulation import playDrive, playLong, playFairway, playShort, playPutt, h_arch, lp_arch, dap_arch, ds_arch
from flask import (Flask, redirect, render_template, request,
                   send_from_directory, url_for, jsonify, json)
from flask_cors import CORS
from environmentSecrets import AZURE_SQL_CONNECTION_STRING
from flask_socketio import SocketIO, emit, join_room, leave_room, send

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
CORS(app,resources={r"/*":{"origins":"*"}})
socketio = SocketIO(app,cors_allowed_origins="*")

# app = Flask(__name__)
# CORS(app)
# app.config['SECRET_KEY'] = 'stselab'
# socketio = SocketIO(app)
# socketio.init_app(app, cors_allowed_origins="*")

# Temporary global variables before database is connected
# serverStorageCount = 0
# users = [] # May still be usefulf for watching and printing data in compared to data in db, but not currently used.

@app.route('/')
def index():
   print('Request for index page received')
   return render_template('index.html')

@app.route('/ws')
def websocket():
   print('Request for websocket page received')
   return render_template('websocket.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/hello', methods=['POST'])
def hello():
   name = request.form.get('name')
   if name:
       print('Request for hello page received with name=%s' % name)
       return render_template('hello.html', name = name)
   else:
       print('Request for hello page received with no name or blank name -- redirecting')
       return redirect(url_for('index'))
   
# All real methods to be used by application:
    
# Needed endpoints:
    # Principally: Status session (for all)
    # begin game (for hosts)
    # join game (for players)
    # remove player (for hosts)
    # leave session (for players)
    # end tournament (for hosts) OR maybe don't allow them to end early as it could make data collection weirder?
    # begin round (for hosts)
    # end round (for hosts) - may need to forcibly close rounds even if players aren't done
        # TODO work on session dates, make them actual UTC timestamps, and switch to using startDate to be when the tournament has started
        # So that no players can join a session partly through. Then use the endDate so that the front-end polling the session can know
        # when the session is over. Also use round to tell what round the session is on (or could just make round 0 and round 4 represent
        # start and end time and not need those fields, but may be nice to have when the sessions actually happened). 
    # record hole result (for all)
        # TODO BE serves as a path to hit Plumber R code as it is over http, could have backend directly save results rather than FE making a second call to BE to save them.
        # Such as round #, solvers, etc, and will call R then record hole, otherwise just save results from FE
    # get scores for round for session (for all)
    # get scores for all 3 rounds for session (for all)
    # get aggregate scores for all sessions (for all)
    # get aggregate scores for for a player (for all) ? Maybe not needed and not sure exactly what it would look like

# REST API Endpoints:

# Routing for endpoints so this file isn't out of hand
   
# Session routes handled in session.py
app.add_url_rule('/session/status', 'session/status', sessionStatus, methods=['POST'])
app.add_url_rule('/session/players', 'session/players', playersInSession, methods=['POST'])
app.add_url_rule('/session/end', 'session/end', endSession, methods=['POST'])
app.add_url_rule('/session/advance', 'session/advance', advanceSession, methods=['POST'])
app.add_url_rule('/session/roundresults', 'session/roundresults', roundResults, methods=['POST'])
app.add_url_rule('/session/finalresults', 'session/finalresults', finalResults, methods=['POST'])
app.add_url_rule('/session/surveyssubmitted', 'session/surveyssubmitted', surveysSubmitted, methods=['POST'])

# User routes handled in users.py
app.add_url_rule('/player/host', 'player/host', host, methods=['POST'])
app.add_url_rule('/player/join', 'player/join', join, methods=['POST'])
app.add_url_rule('/player/roundResult', 'player/roundResult', roundResult, methods=['POST'])
app.add_url_rule('/player/remove', 'player/remove', remove, methods=['POST'])
app.add_url_rule('/player/freeRoamResult', 'player/freeRoamResult', freeRoamResult, methods=['POST'])
app.add_url_rule('/player/freeRoamSurvey', 'player/freeRoamSurvey', freeRoamSurvey, methods=['POST'])
app.add_url_rule('/player/allResults', 'player/allResults', allResults, methods=['GET'])

# Deployed Simulation is only avialable via http, so the front-end cannot make requests to it 
# as it would be mixed content. Without a registered domain name and SSL certificate the droplet
# it is hosted on cannot be made into an https API. Therefore calls must come from the backend, so 
# the front end will make requests here just to pass them on to the simulation.
# simulation routes handled in simulation.py
app.add_url_rule('/playDrive', 'playDrive', playDrive, methods=['POST'])
app.add_url_rule('/playLong', 'playLong', playLong, methods=['POST'])
app.add_url_rule('/playFairway', 'playFairway', playFairway, methods=['POST'])
app.add_url_rule('/playShort', 'playShort', playShort, methods=['POST'])
app.add_url_rule('/playPutt', 'playPutt', playPutt, methods=['POST'])
app.add_url_rule('/h_arch', 'h_arch', h_arch, methods=['POST'])
app.add_url_rule('/lp_arch', 'lp_arch', lp_arch, methods=['POST'])
app.add_url_rule('/dap_arch', 'dap_arch', dap_arch, methods=['POST'])
app.add_url_rule('/ds_arch', 'ds_arch', ds_arch, methods=['POST'])


# # TODO may switch to websocket connection for backend with https://flask-socketio.readthedocs.io/en/latest/
# # Websocket endpoints:
# # Using websockets allows server to send messages, so clients do not have to continually poll for updates.
# # The updates that the server may need to send are:
#     # A player has joined a session,
#     # A player has left a session,
#     # And the session status changing (starting, round changing, ending)


# # Websocket event catchers:

# # Will be using names instead of namespaces I believe

# @socketio.on('join')
# def on_join(data):
#     username = data['username']
#     room = data['room']
#     join_room(room)
#     send(username + ' has entered the room.', to=room)

# @socketio.on('leave')
# def on_leave(data):
#     username = data['username']
#     room = data['room']
#     leave_room(room)
#     send(username + ' has left the room.', to=room)

# # When a message is sent with the broadcast option enabled, all clients connected to the namespace receive it, including the sender. When namespaces are not used, the clients connected to the global namespace receive the message. 

# # The socketio.send() and socketio.emit() methods can be used to broadcast to all connected clients BASED on events that happen server side. The context-free socketio.send() and socketio.emit() functions also accept a to argument to broadcast to all clients in a room. All clients are assigned a room when they connect, named with the session ID of the connection, which can be obtained from request.sid
# # socketio.emit("emitting to the rooom", to=request.sid)

# # handles custom event called "my_custom_event" with 3 arguments (num of args can be anything)
# @socketio.event
# def my_custom_event(arg1, arg2, arg3):
#     print('received args: ' + arg1 + arg2 + arg3)
#     # Use emit for custom events
#     # by default will use namespace of incoming message, but 
#     # namespace can also be specified (Like group)
#     # emit('my response', json)
#     # To send an event with multiple arguments, send a tuple:
#     # emit('my response', ('foo', 'bar', json), namespace='/chat')
#     # Broadcast to entire namespace via
#     emit('my response', json, broadcast=True)

# # on_event method allows separate function definition
# def my_function_handler():
#     socketio.emit("Hello room!", to=request.sid)

# socketio.on_event('say hi to room', my_function_handler)

# # Catches unnamed events with string messages
# @socketio.on('message')
# def handle_message(data):
#     print('received message: ' + data)
#     send(data)

# # catches unnamed events with json messages
# @socketio.on('json')
# def handle_json(json):
#     print('received json: ' + str(json))
#     send(json, json=True)

# # Connection events: (probably unnecessary but I want them for logging)
# @socketio.on('connect')
# def test_connect():
#     print('Client connected')
#     emit('my response', {'data': 'Connected'})

# @socketio.on('disconnect')
# def test_disconnect():
#     print('Client disconnecting')
#     print('Client disconnected')
    

# if __name__ == '__main__':
#     socketio.run(app)


@app.route("/http-call")
def http_call():
    """return JSON with string data as the value"""
    data = {'data':'This text was fetched using an HTTP call to server on render'}
    return jsonify(data)

@socketio.on("connect")
def connected():
    """event listener when client connects to the server"""
    print(request.sid)
    print("client has connected")
    emit("connect",{"data":f"id: {request.sid} is connected"})

@socketio.on("custom event 1")
def custom_event_1(data):
    """event listener when client emits a custom event"""
    print("custom event 1: ",data)
    if (data == "ping"):
        emit("custom event 1","pong",broadcast=True)
    else: 
        emit("custom event 1","wrong",broadcast=True)

@socketio.on('data')
def handle_message(data):
    """event listener when client types a message"""
    print("data from the front end: ",str(data))
    emit("data",{'data':data,'id':request.sid},broadcast=True)

@socketio.on("disconnect")
def disconnected():
    """event listener when client disconnects to the server"""
    print("user disconnected")
    emit("disconnect",f"user {request.sid} disconnected",broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True,port=5000)