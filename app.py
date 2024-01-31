import os
import pyodbc 
import random
import uuid
from dotenv import load_dotenv
load_dotenv()
from datetime import datetime

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
   
# Test routes, TODO should add health checks for monitoring and deployment purposes

@app.route('/testdb')
def testdb():
    # ODBC works for local windows maching with ODBC Driver 18. Change to Driver={FreeTDS} for deployed Linux
    # driver_string = 'Driver={ODBC Driver 18 for SQL Server};' if os.name == 'nt' else 'Driver={FreeTDS};'
    # connection_string = driver_string + os.getenv('AZURE_SQL_CONNECTIONSTRING')
    try:
        # Create connection to SQL Database
        conn = pyodbc.connect(AZURE_SQL_CONNECTION_STRING, timeout=120)
        cursor = conn.cursor()
        totalString = "players are: "
        # Execute SQL query and build result
        cursor.execute("SELECT * FROM Player")
        for row in cursor.fetchall():
            totalString += row.FirstName + " " + row.color + ", "
        return jsonify({"people": totalString})
    except Exception as e:
        return jsonify({"error": str(e)})



# All real methods to be used by application:

# TODO set up routing and controllers so this file isn't out of hand
    
# TODO Needed endpoints:
    # Principally: Status session

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
    
# Status a session, includes retreiving all players in a session and all scores for each player
# This will be called repeatedly by polling front-end, and so switching to websockets would reduce the work
# needed to be done by the server.
# TODO even if I do keep polling, I could break this down into getting session, getting all players, and getting scores, so that
# only the work of checking session round has to be done constantly. 
@app.route('/session/status', methods=['POST'])
def sessionStatus():
    try:
        # First check that required data is in request, must have valid sessionId
        data = request.json
        sessionId = data.get('sessionId')
        playerId = data.get('playerId')

        # Create connection to Azure SQL Database
        conn = pyodbc.connect(AZURE_SQL_CONNECTION_STRING, timeout=120)
        cursor = conn.cursor()

        # Save information about session itself
        cursor.execute(f"SELECT * FROM Session WHERE JoinCode = ?", (str(sessionId)))
        session = cursor.fetchone()
        if session is None:
            return jsonify({"error": "Session not found"})
        
        # Checking that player is still in their current session (they may have been kicked by host)
        cursor.execute(f"SELECT * FROM Player WHERE Id = ?", (str(playerId)))
        player = cursor.fetchone()
        if player and str(player.SessionId) != str(sessionId):
            return jsonify({"error": "Player not in session"})

        # Check that players exist with matching sessionId
        cursor.execute(f"SELECT * FROM Player WHERE SessionId = ?", (str(sessionId)))
        players = cursor.fetchall()
        if not players:
            return jsonify({"error": "Players not found"})
        
        # Save array of all players in the session
        playerList = []
        for player in players:
            playerList.append({"id": player.Id, "firstName": player.FirstName, "color": player.Color, "scores": []})
            # For each player, also save their scores
            cursor.execute(f"SELECT * FROM RoundResult WHERE PlayerId = ?", (str(player.Id)))
            scores = cursor.fetchall()
            if scores:
                for score in scores:
                    playerList[-1]["scores"].append({"shots": score.Shots, "cost": score.Cost, "round": score.Round})

        return jsonify({"success": True, "players": playerList, 
                        "session": {"startDate": session.StartDate, "endDate": session.EndDate, "round": session.Round}})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}) 

# Begins a new game by a host, creating a session. Will need all of the information collected for each player, without
# a join code. Must return if successful or not, and if successful, the join code for the session.
@app.route('/player/host', methods=['POST'])
def host():
    try:
        # TODO decide on exact data wanted for each player
        # First check that required data is in request
        data = request.json
        firstName = data.get('firstName')
        color = data.get('color')

        # Create connection to Azure SQL Database
        conn = pyodbc.connect(AZURE_SQL_CONNECTION_STRING, timeout=120)
        cursor = conn.cursor()

        # Now generate a join code and create a new session in the database
        joinCode = random.randint(100000, 999999)
        # check join code doesn't already exist in database
        newCode = False
        while not newCode:
            cursor.execute(f"SELECT * FROM Session WHERE JoinCode = ?", (str(joinCode)))
            if cursor.fetchone() is None:
                newCode = True
            else:
                joinCode = random.randint(100000, 999999)

        # Insert new session into database
        cursor.execute(f"INSERT INTO Session (JoinCode, Round, StartDate, EndDate) VALUES (?, 0, ?, ?)",
            (str(joinCode), datetime.today().strftime('%Y-%m-%d %H:%M:%S'), 'None'))
        conn.commit()

        # Generate UUID for player
        playerId = uuid.uuid4()

        # Now create new player and insert them into the database
        cursor.execute(f"INSERT INTO Player (Id, FirstName, Color, SessionId) VALUES (?, ?, ?, ?)", 
            (playerId, firstName, color, str(joinCode)))  
        conn.commit()

        # On success return success and join code
        return jsonify({"success": True, "joinCode": joinCode, "playerId": playerId})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})
    
# Joins a game creating a player for a given session IF that session exists
@app.route('/player/join', methods=['POST'])
def join():
    try:
        # TODO decide on exact data wanted for each player
        # First check that required data is in request, must have valid join code
        data = request.json
        firstName = data.get('firstName')
        color = data.get('color')
        joinCode = data.get('joinCode')

        # Create connection to Azure SQL Database
        conn = pyodbc.connect(AZURE_SQL_CONNECTION_STRING, timeout=120)
        cursor = conn.cursor()

        # Check that session exists
        cursor.execute(f"SELECT * FROM Session WHERE JoinCode = ?", (str(joinCode)))
        session = cursor.fetchone()
        if session is None:
            return jsonify({"error": "Session not found"})
        
        # Check that session hasn't already started (Should still be on round 0)
        if session.Round != 0:
            return jsonify({"error": "Session has already started"})

        # Generate UUID for player
        playerId = uuid.uuid4()

        # Now create new player and insert them into the database
        cursor.execute(f"INSERT INTO Player (Id, FirstName, Color, SessionId) VALUES (?, ?, ?, ?)", 
            (playerId, firstName, color, str(joinCode)))  
        conn.commit()

        return jsonify({"success": True, "playerId": playerId})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})
    
# Removes a player from a session, called by the host to remove them or the player themselves to leave
# TODO must decide if it should delete the player data from the database (and all reliant round results) 
# or just change the session id to null. Will start with just changing session id so data remains in db
# for aggregate results.
@app.route('/player/remove', methods=['POST'])
def remove():
    try:
        # First check that required data is in request, must have valid playerId
        data = request.json
        playerId = data.get('playerId')

        # Create connection to Azure SQL Database
        conn = pyodbc.connect(AZURE_SQL_CONNECTION_STRING, timeout=120)
        cursor = conn.cursor()

        # Ensure player exists
        cursor.execute(f"SELECT * FROM Player WHERE Id = ?", (str(playerId)))
        player = cursor.fetchone()
        if player is None:
            return jsonify({"error": "Player not found"})
        
        cursor.execute(f"UPDATE Player SET SessionId = Null WHERE Id = ?", str(playerId))
        conn.commit()

        return jsonify({"success": True})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})

# Joins a game creating a player for a given session IF that session exists
@app.route('/player/result', methods=['POST'])
def result():
    try:
        # Save player's results for a round in the tournament
        # First check that required data is in request, must have valid Id for Player,
        # as well as shot, cost, and round information
        data = request.json
        id = data.get('playerId')
        shots = data.get('shots')
        cost = data.get('cost')
        round = data.get('round')

        # Create connection to Azure SQL Database
        conn = pyodbc.connect(AZURE_SQL_CONNECTION_STRING, timeout=120)
        cursor = conn.cursor()

        # Check that player exists
        cursor.execute(f"SELECT * FROM Player WHERE Id = ?", (str(id)))
        player = cursor.fetchone()
        if player is None:
            return jsonify({"error": "Player not found"})
        
        print(f"SQL For saving result: INSERT INTO RoundResult (PlayerId, Shots, Cost, Round) VALUES (?, ?, ?, ?)", (str(id), str(shots), str(cost), str(round)))

        # Now create new Round Result and insert into its table
        cursor.execute(f"INSERT INTO RoundResult (PlayerId, Shots, Cost, Round) VALUES (?, ?, ?, ?)", 
                       (str(id), str(shots), str(cost), str(round)))  
        conn.commit()

        return jsonify({"success": True})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})
    

# Moves session to the next round, only host can call this
# Will update the round number, and the EndDate if the last round has been played
@app.route('/session/advance', methods=['POST'])
def advanceSession():
    try:
        # First check that required data is in request, must have valid sessionId
        data = request.json
        sessionId = data.get('sessionId')

        # Create connection to Azure SQL Database
        conn = pyodbc.connect(AZURE_SQL_CONNECTION_STRING, timeout=120)
        cursor = conn.cursor()

        # Ensure session exists
        cursor.execute(f"SELECT * FROM Session WHERE JoinCode = ?", (str(sessionId)))
        session = cursor.fetchone()
        if session is None:
            return jsonify({"error": "Session not found"})
        
        cursor.execute(f"UPDATE Session SET Round = ? WHERE JoinCode = ?", (str(session.Round + 1), str(sessionId)))
        conn.commit()

        return jsonify({"success": True, "round": session.Round + 1})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})


# TODO may switch to websocket connection for backend with https://flask-socketio.readthedocs.io/en/latest/
# Websocket endpoints:
# Using websockets allows server to send messages, so clients do not have to continually poll for updates.
# The updates that the server may need to send are:
    # A player has joined a session,
    # A player has left a session,
    # And the session status changing (starting, round changing, ending)


if __name__ == '__main__':
    app.run()
