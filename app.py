import os
from dotenv import load_dotenv
load_dotenv()

import requests
from users import host, join, roundResult, remove, freeRoamResult, freeRoamSurvey
from session import sessionStatus, advanceSession
from simulation import playDrive, playLong, playFairway, playShort, playPutt, h_arch, lp_arch, dap_arch, ds_arch
from flask import (Flask, redirect, render_template, request,
                   send_from_directory, url_for, jsonify, json)
from flask_cors import CORS
from environmentSecrets import AZURE_SQL_CONNECTION_STRING

app = Flask(__name__)
CORS(app)

# Temporary global variables before database is connected
serverStorageCount = 0
users = [] # May still be usefulf for watching and printing data in compared to data in db, but not currently used.

@app.route('/')
def index():
   print('Request for index page received')
   return render_template('index.html')

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
        # TODO decide if FE or BE hits Plumber, if BE then endpoint for recording hole will take in all necessary params
        # Such as round #, solvers, etc, and will call R then record hole, otherwise just save results from FE
    # get scores for round for session (for all)
    # get scores for all 3 rounds for session (for all)
    # get aggregate scores for all sessions (for all)
    # get aggregate scores for for a player (for all) ? Maybe not needed and not sure exactly what it would look like

# REST API Endpoints:

# Routing for endpoints so this file isn't out of hand
   
# Session routes handled in session.py
app.add_url_rule('/session/status', 'session/status', sessionStatus, methods=['POST'])
app.add_url_rule('/session/advance', 'session/advance', advanceSession, methods=['POST'])

# User routes handled in users.py
app.add_url_rule('/player/host', 'player/host', host, methods=['POST'])
app.add_url_rule('/player/join', 'player/join', join, methods=['POST'])
app.add_url_rule('/player/roundResult', 'player/roundResult', roundResult, methods=['POST'])
app.add_url_rule('/player/remove', 'player/remove', remove, methods=['POST'])
app.add_url_rule('/player/freeRoamResult', 'player/freeRoamResult', freeRoamResult, methods=['POST'])
app.add_url_rule('/player/freeRoamSurvey', 'player/freeRoamSurvey', freeRoamSurvey, methods=['POST'])

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


# TODO may switch to websocket connection for backend with https://flask-socketio.readthedocs.io/en/latest/
# Websocket endpoints:
# Using websockets allows server to send messages, so clients do not have to continually poll for updates.
# The updates that the server may need to send are:
    # A player has joined a session,
    # A player has left a session,
    # And the session status changing (starting, round changing, ending)


if __name__ == '__main__':
    app.run()
