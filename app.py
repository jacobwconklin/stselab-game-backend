import os
import pyodbc 
import random
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
   

# STSELab Demo Methods:
@app.route('/addcount')
def addCount():
    global serverStorageCount
    serverStorageCount += 1
    return jsonify({"count": serverStorageCount})

@app.route('/submitform', methods=['POST'])
def submitform():
    try:
        data = request.json
        firstName = data.get('firstName')
        lastName = data.get('lastName')
        num = data.get('num')
        birthDate = data.get('birthDate')
        pet = data.get('pet')
        color = data.get('color')
        global users
        newUser = {"id": len(users) + 1, "firstName": firstName, "lastName": lastName, "num": num, "birthDate": birthDate, "pet": pet, "color": color}
        users.append(newUser)
        return jsonify({"success": True, "user": newUser})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})
    
@app.route('/allusers')
def allusers():
    global users
    return jsonify({"users": users})

@app.route('/resetusers')
def resetusers():
    global users
    users = []
    return jsonify({"success": True})

@app.route('/testdb')
def testdb():
    # ODBC works for local windows maching with ODBC Driver 18. Change to Driver={FreeTDS} for deployed Linux
    # driver_string = 'Driver={ODBC Driver 18 for SQL Server};' if os.name == 'nt' else 'Driver={FreeTDS};'
    # connection_string = driver_string + os.getenv('AZURE_SQL_CONNECTIONSTRING')
    try:
        # Create connection to SQL Database
        conn = pyodbc.connect(AZURE_SQL_CONNECTION_STRING, timeout=120)
        cursor = conn.cursor()
        totalString = "people are: "
        # Execute SQL query and build result
        cursor.execute("SELECT * FROM TestUsers")
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

# Begins a new game by a host, creating a session. Will need all of the information collected for each player, without
# a join code. Must return if successful or not, and if successful, the join code for the session.
@app.route('/host', methods=['POST'])
def host():
    try:
        # TODO decide on exact data wanted for each player
        # First check that required data is in request
        data = request.json
        firstName = data.get('firstName')
        color = data.get('color')

        # Now generate a join code and create a new session in the database
        joinCode = random.randint(100000, 999999)
        # TODO check join code doesn't already exist in database

        # Create connection to Azure SQL Database
        conn = pyodbc.connect(AZURE_SQL_CONNECTION_STRING, timeout=120)
        cursor = conn.cursor()

        # Insert new session into database
        cursor.execute(f"SET IDENTITY_INSERT Session ON INSERT INTO Session (joinCode, startDate, endDate) VALUES (?, ?, ?)",
            (str(joinCode), datetime.today().strftime('%Y-%m-%d'), 'None'))
        conn.commit()

        # Now create new user and insert them into the database
        cursor.execute(f"INSERT INTO TestUsers (firstName, sessionId, color) VALUES (?, ?, ?)", (firstName, str(joinCode), color))  
        conn.commit()

        # On success return success and join code
        return jsonify({"success": True, "joinCode": joinCode})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})
    
# Joins a game creating a player for a given session IF that session exists
@app.route('/join', methods=['POST'])
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
        cursor.execute(f"SELECT * FROM Session WHERE joinCode = ?", (str(joinCode)))
        session = cursor.fetchone()
        if session is None:
            return jsonify({"error": "Session not found"})

        # Now create new user and insert them into the database
        cursor.execute(f"INSERT INTO TestUsers (firstName, sessionId, color) VALUES (?, ?, ?)", (firstName, str(joinCode), color))  
        conn.commit()

        return jsonify({"success": True})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})

# Retreives all players in a given Session
@app.route('/session/players', methods=['POST'])
def sessionPlayers():
    try:
        # First check that required data is in request, must have valid sessionId
        data = request.json
        sessionId = data.get('sessionId')

        # Create connection to Azure SQL Database
        conn = pyodbc.connect(AZURE_SQL_CONNECTION_STRING, timeout=120)
        cursor = conn.cursor()

        # Check that players exist with matching sessionId
        cursor.execute(f"SELECT * FROM TestUsers WHERE sessionId = ?", (str(sessionId)))
        players = cursor.fetchall()
        if not players:
            return jsonify({"error": "Players not found"})
        
        playerList = []
        for player in players:
            print(player.firstName)
            playerList.append({"id": player.id, "firstName": player.firstName, "color": player.color})

        return jsonify({"success": True, "players": playerList})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}) 


if __name__ == '__main__':
    app.run()
