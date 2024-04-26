import os
from dotenv import load_dotenv
load_dotenv()

import requests
from users import host, join, roundResult, remove, freeRoamResult, freeRoamSurvey, allResults, armRoundResult, diceResult
from session import sessionStatus, advanceSession, roundResults, finalResults, surveysSubmitted, playersInSession, endSession, armFinalResults, armRoundResults
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
   
# TODO: Function to save data from a session, potentially with different settings for what to include (currently manually pulling and saving csv's from Azure) 
# Saves all data from a given session to a local file
# Only uncomment this out to run on local machine, do not use in production, as files would just get saved to the server and be 
# un-retrievable by a user. 
# @app.route('/saveSession', methods=['POST'])
# def saveSession():
#     try:
#         # First check that required data is in request, must have valid sessionId
#         data = request.json
#         sessionId = data.get('sessionId')

#         # Create connection to Azure SQL Database
#         conn = pyodbc.connect(AZURE_SQL_CONNECTION_STRING, timeout=120)
#         cursor = conn.cursor()
        
#         # Check that players exist with matching sessionId
#         cursor.execute(f"SELECT * FROM PlayerBrief WHERE SessionId = ?", (str(sessionId)))
#         players = cursor.fetchall()
#         if not players:
#             return jsonify({"error": "Players not found"})
        
#         # Save array of all players in the session
#         playerList = []
#         for player in players:
#             playerList.append({"id": player.Id, "name": player.Name, "color": player.Color, "scores": []})
#             # For each player, also save their scores
#             cursor.execute(f"SELECT * FROM RoundResult WHERE PlayerId = ? AND Round > 5", (str(player.Id)))
#             scores = cursor.fetchall()
#             if scores:
#                 for score in scores:
#                     playerList[-1]["scores"].append({"shots": score.Shots, "cost": score.Cost, "score": score.Score, "round": score.Round,
#                         "solverOne": getattr(score, 'SolverOne', False), "solverTwo": getattr(score, 'SolverTwo', False),
#                         "solverThree": getattr(score, 'SolverThree', False), "architecture": score.Architecture})
        
#         with open(str(sessionId) + '-session-data.json', 'w') as f:
#             json.dump(data, f)
#         return jsonify({"success": True})
#     except Exception as e:
#         print(e)
#         return jsonify({"error": str(e)})
   
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
# Mechanical Arm Mission:
app.add_url_rule('/session/armroundresults', 'session/armroundresults', armRoundResults, methods=['POST'])
app.add_url_rule('/session/armfinalresults', 'session/armfinalresults', armFinalResults, methods=['POST'])

# User routes handled in users.py
app.add_url_rule('/player/host', 'player/host', host, methods=['POST'])
app.add_url_rule('/player/join', 'player/join', join, methods=['POST'])
app.add_url_rule('/player/roundResult', 'player/roundResult', roundResult, methods=['POST'])
app.add_url_rule('/player/remove', 'player/remove', remove, methods=['POST'])
app.add_url_rule('/player/freeRoamResult', 'player/freeRoamResult', freeRoamResult, methods=['POST'])
app.add_url_rule('/player/freeRoamSurvey', 'player/freeRoamSurvey', freeRoamSurvey, methods=['POST'])
app.add_url_rule('/player/diceResult', 'player/diceResult', diceResult, methods=['POST'])
app.add_url_rule('/player/allResults', 'player/allResults', allResults, methods=['GET'])
# Mechanical Arm Mission:
app.add_url_rule('/player/armRoundResult', 'player/armRoundResult', armRoundResult, methods=['POST'])

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

if __name__ == '__main__':
    app.run()