# Contains endpoints for session actions

from datetime import datetime
import pyodbc 
from dotenv import load_dotenv
load_dotenv()
from flask import (request, jsonify)
from environmentSecrets import VT_MYSQL_HOST, VT_MYSQL_STSELAB_DB, VT_MYSQL_USER, VT_MYSQL_PASSWORD, VT_MYSQL_PORT, VT_MYSQL_PASSWORD_SALT
import pymysql
import pymysql.cursors

# Status a session, getting back the round the session is on, and the start and end dates of the session.
# This will be called repeatedly by polling front-end, and so switching to websockets would reduce the work
# needed to be done by the server.
# Even though this endpoint is always polled, it only retreives round number so minimal work is required by BE here.
def sessionStatus():
    try:
        db = None
        cursor = None
        db = pymysql.connections.Connection(host=VT_MYSQL_HOST, user=VT_MYSQL_USER, password=VT_MYSQL_PASSWORD, database=VT_MYSQL_STSELAB_DB, port=VT_MYSQL_PORT)

        # First check that required data is in request, must have valid sessionId
        data = request.json
        sessionId = data.get('sessionId')
        playerId = data.get('playerId')

        # Create cursot to perform SQL operations on VTMySQL DB
        cursor = db.cursor(pymysql.cursors.DictCursor)

        # Save information about session itself
        sqlString = f"SELECT * FROM Session WHERE JoinCode = '{sessionId}'"
        cursor.execute(sqlString)
        session = cursor.fetchone()
        if session is None:
            return jsonify({"error": "Session not found"})
        
        # Checking that player is still in their current session (they may have been kicked by host)
        sqlString = f"SELECT * FROM PlayerBrief WHERE Id = '{playerId}'"
        cursor.execute(sqlString)
        player = cursor.fetchone()
        if player and str(player['SessionId']) != str(sessionId):
            return jsonify({"error": "Player not in session"})

        return jsonify({"success": True, "session": {"round": session['Round'], "startDate": session['StartDate'], "endDate": session['EndDate']}})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}) 
    finally:
        if (cursor != None):
            cursor.close()
        if (db != None):
            db.close()
    
# Simply provides a list of players in a session, for now useful in wait room to show all players without any need
# for scores. 
def playersInSession():
    try:
        db = None
        cursor = None
        db = pymysql.connections.Connection(host=VT_MYSQL_HOST, user=VT_MYSQL_USER, password=VT_MYSQL_PASSWORD, database=VT_MYSQL_STSELAB_DB, port=VT_MYSQL_PORT)
        
        # First check that required data is in request, must have valid sessionId
        data = request.json
        sessionId = data.get('sessionId')

        # Create cursot to perform SQL operations on VTMySQL DB
        cursor = db.cursor(pymysql.cursors.DictCursor)

        # Save information about session itself
        sqlString = f"SELECT * FROM Session WHERE JoinCode = '{sessionId}'"
        cursor.execute(sqlString)
        session = cursor.fetchone()
        if session is None:
            return jsonify({"error": "Session not found"})

        # Check that players exist with matching sessionId
        sqlString = f"SELECT * FROM PlayerBrief WHERE SessionId = '{sessionId}'"
        cursor.execute(sqlString)
        players = cursor.fetchall()
        if not players:
            return jsonify({"error": "Players not found"})
        
        # Save array of all players in the session
        playerList = []
        completedOnboarding = []
        for player in players:
            # Check for players that have finished the onboarding Dice game
            sqlString = f"SELECT * FROM DiceResult WHERE PlayerId = '{player['Id']}'"
            cursor.execute(sqlString)
            diceResult = cursor.fetchone()
            didCompleteOnboarding = False
            if diceResult:
                completedOnboarding.append(str(player['Id']))
                didCompleteOnboarding = True
            # Save player information
            playerList.append({"id": player['Id'], "name": player['Name'], "color": player['Color'], "completedOnboarding": didCompleteOnboarding})

        return jsonify({"success": True, "players": playerList, "completedOnboarding": completedOnboarding})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})
    finally:
        if (cursor != None):
            cursor.close()
        if (db != None):
            db.close()
    
# applies end time to session, could be used to allow players in final results page to stop polling backend, also saves end time into 
# database.
def endSession():
    try:
        db = None
        cursor = None
        db = pymysql.connections.Connection(host=VT_MYSQL_HOST, user=VT_MYSQL_USER, password=VT_MYSQL_PASSWORD, database=VT_MYSQL_STSELAB_DB, port=VT_MYSQL_PORT)
        
        # First check that required data is in request, must have valid sessionId
        data = request.json
        sessionId = data.get('sessionId')

        # Create cursot to perform SQL operations on VTMySQL DB
        cursor = db.cursor(pymysql.cursors.DictCursor)

        # Save information about session itself
        sqlString = f"SELECT * FROM Session WHERE JoinCode = '{sessionId}'"
        cursor.execute(sqlString)
        session = cursor.fetchone()
        if session is None:
            return jsonify({"error": "Session not found"})
        
        # Update the end date of the session
        # Uses UTC date by putting CURRENT_TIMESTAMP() in the query
        sqlString = f"UPDATE Session SET EndDate = CURRENT_TIMESTAMP() WHERE JoinCode = '{sessionId}'"
        cursor.execute(sqlString)
        db.commit()

        return jsonify({"success": True})
    except Exception as e:
            print(e)
            return jsonify({"error": str(e)})
    finally:
        if (cursor != None):
            cursor.close()
        if (db != None):
            db.close()
    
    
# Moves session to the next round, only host can call this
# Will update the round number, and the EndDate if the last round has been played
def advanceSession():
    try:
        db = None
        cursor = None
        db = pymysql.connections.Connection(host=VT_MYSQL_HOST, user=VT_MYSQL_USER, password=VT_MYSQL_PASSWORD, database=VT_MYSQL_STSELAB_DB, port=VT_MYSQL_PORT)
        
        # First check that required data is in request, must have valid sessionId
        # I have decided on using round number to determine position in the game. 
        data = request.json
        sessionId = data.get('sessionId')

        # Create cursot to perform SQL operations on VTMySQL DB
        cursor = db.cursor(pymysql.cursors.DictCursor)

        # Ensure session exists
        sqlString = f"SELECT * FROM Session WHERE JoinCode = '{sessionId}'"
        cursor.execute(sqlString)
        session = cursor.fetchone()
        if session is None:
            return jsonify({"error": "Session not found"})
        
        newRoundNumber = session['Round'] + 1
        sqlString = f"UPDATE Session SET Round = '{newRoundNumber}' WHERE JoinCode = '{sessionId}'"
        cursor.execute(sqlString)
        db.commit()

        return jsonify({"success": True, "round": session['Round'] + 1})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})
    finally:
        if (cursor != None):
            cursor.close()
        if (db != None):
            db.close()
    
# Endpoint to get results for for a round rather than shoving results into session status
def roundResults():
    try:
        db = None
        cursor = None
        db = pymysql.connections.Connection(host=VT_MYSQL_HOST, user=VT_MYSQL_USER, password=VT_MYSQL_PASSWORD, database=VT_MYSQL_STSELAB_DB, port=VT_MYSQL_PORT)
        
        # First check that required data is in request, must have valid sessionId
        data = request.json
        sessionId = data.get('sessionId')
        round = data.get('round')

        # Create cursot to perform SQL operations on VTMySQL DB
        cursor = db.cursor(pymysql.cursors.DictCursor)
        
        # Check that players exist with matching sessionId
        sqlString = f"SELECT * FROM PlayerBrief WHERE SessionId = '{sessionId}'"
        cursor.execute(sqlString)
        players = cursor.fetchall()
        if not players:
            return jsonify({"error": "Players not found"})
        
        # Save array of all players in the session
        # players = [
        #     {"id": 1, "name": "Player 1", "color": "red", "shots": 50, "cost": 100, "solverOne": 0, "solverTwo": 2, "architecture": "h" },
        # ]
        playerList = []
        for player in players:
            playerList.append({"id": player['Id'], "name": player['Name'], "color": player['Color']})
            # For each player, also save their scores, solvers, and architecture
            sqlString = f"SELECT * FROM RoundResult WHERE PlayerId = '{str(player['Id'])}' AND Round = '{str(round)}'"
            cursor.execute(sqlString)
            score = cursor.fetchone()
            if score:
                playerList[-1]["shots"] = score['Shots']
                playerList[-1]["cost"] = score['Cost']
                playerList[-1]["solverOne"] = getattr(score, 'SolverOne', None)
                playerList[-1]["solverTwo"] = getattr(score, 'SolverTwo', None)
                playerList[-1]["solverThree"] = getattr(score, 'SolverThree', None)
                playerList[-1]["architecture"] = score['Architecture']
                playerList[-1]["score"] = score['Score']
                playerList[-1]["customPerformanceWeight"] = getattr(score, 'CustomPerformanceWeight', None)

        return jsonify({"success": True, "results": playerList})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})
    finally:
        if (cursor != None):
            cursor.close()
        if (db != None):
            db.close()
    
# Get aggregate results of all tournament rounds
def finalResults():
    try:
        db = None
        cursor = None
        db = pymysql.connections.Connection(host=VT_MYSQL_HOST, user=VT_MYSQL_USER, password=VT_MYSQL_PASSWORD, database=VT_MYSQL_STSELAB_DB, port=VT_MYSQL_PORT)
        
        # First check that required data is in request, must have valid sessionId
        data = request.json
        sessionId = data.get('sessionId')

        # Create cursot to perform SQL operations on VTMySQL DB
        cursor = db.cursor(pymysql.cursors.DictCursor)
        
        # Check that players exist with matching sessionId
        sqlString = f"SELECT * FROM PlayerBrief WHERE SessionId = '{sessionId}'"
        cursor.execute(sqlString)
        players = cursor.fetchall()
        if not players:
            return jsonify({"error": "Players not found"})
        
        # Save array of all players in the session
        playerList = []
        for player in players:
            playerList.append({"id": player['Id'], "name": player['Name'], "color": player['Color'], "scores": []})
            # For each player, also save their scores
            sqlString = f"SELECT * FROM RoundResult WHERE PlayerId = '{str(player['Id'])}' AND Round > 5"
            cursor.execute(sqlString)
            scores = cursor.fetchall()
            if scores:
                for score in scores:
                    playerList[-1]["scores"].append({"shots": score['Shots'], "cost": score['Cost'], "score": score['Score'], "round": score['Round'],
                        "solverOne": getattr(score, 'SolverOne', False), "solverTwo": getattr(score, 'SolverTwo', False),
                        "solverThree": getattr(score, 'SolverThree', False), "architecture": score['Architecture']})

        return jsonify({"success": True, "results": playerList})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})
    finally:
        if (cursor != None):
            cursor.close()
        if (db != None):
            db.close()
    

# Endpoint to get results for for a Mechanical Arm Mission round rather than shoving results into session status
def armRoundResults():
    try:
        db = None
        cursor = None
        db = pymysql.connections.Connection(host=VT_MYSQL_HOST, user=VT_MYSQL_USER, password=VT_MYSQL_PASSWORD, database=VT_MYSQL_STSELAB_DB, port=VT_MYSQL_PORT)
        
        # First check that required data is in request, must have valid sessionId
        data = request.json
        sessionId = data.get('sessionId')
        round = data.get('round')


        # Create cursot to perform SQL operations on VTMySQL DB
        cursor = db.cursor(pymysql.cursors.DictCursor)
        
        # Check that players exist with matching sessionId
        sqlString = f"SELECT * FROM PlayerBrief WHERE SessionId = '{sessionId}'"
        cursor.execute(sqlString)
        players = cursor.fetchall()
        if not players:
            return jsonify({"error": "Players not found"})
        
        # Save array of all players in the session
        # players = [
        #     {"id": 1, "name": "Player 1", "color": "red", "weight": 50, "cost": 100, "solverOne": 0, "solverTwo": 2, "architecture": "Manipulator and Grabber" },
        # ]
        playerList = []
        for player in players:
            playerList.append({"id": player['Id'], "name": player['Name'], "color": player['Color']})
            # For each player, also save their scores, solvers, and architecture
            sqlString = f"SELECT * FROM ArmRoundResult WHERE PlayerId = '{str(player['Id'])}' AND Round = '{str(round)}'"
            cursor.execute(sqlString)
            score = cursor.fetchone()
            if score:
                playerList[-1]["weight"] = score['Grams']
                playerList[-1]["cost"] = score['Cost']
                playerList[-1]["solverOne"] = getattr(score, 'SolverOne', None)
                playerList[-1]["solverTwo"] = getattr(score, 'SolverTwo', None)
                playerList[-1]["solverThree"] = getattr(score, 'SolverThree', None)
                playerList[-1]["solverFour"] = getattr(score, 'SolverFour', None)
                playerList[-1]["architecture"] = score['Architecture']
                playerList[-1]["score"] = score['Score']

        return jsonify({"success": True, "results": playerList})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})
    finally:
        if (cursor != None):
            cursor.close()
        if (db != None):
            db.close()
    
# Get aggregate results of all mechanical arm mission rounds
def armFinalResults():
    try:
        db = None
        cursor = None
        db = pymysql.connections.Connection(host=VT_MYSQL_HOST, user=VT_MYSQL_USER, password=VT_MYSQL_PASSWORD, database=VT_MYSQL_STSELAB_DB, port=VT_MYSQL_PORT)
        
        # First check that required data is in request, must have valid sessionId
        data = request.json
        sessionId = data.get('sessionId')

        # Create cursot to perform SQL operations on VTMySQL DB
        cursor = db.cursor(pymysql.cursors.DictCursor)
        
        # Check that players exist with matching sessionId
        sqlString = f"SELECT * FROM PlayerBrief WHERE SessionId = '{sessionId}'"
        cursor.execute(sqlString)
        players = cursor.fetchall()
        if not players:
            return jsonify({"error": "Players not found"})
        
        # Save array of all players in the session
        playerList = []
        for player in players:
            playerList.append({"id": player['Id'], "name": player['Name'], "color": player['Color'], "scores": []})
            # For each player, also save their scores
            sqlString = f"SELECT * FROM ArmRoundResult WHERE PlayerId = '{str(player['Id'])}'"
            cursor.execute(sqlString)
            scores = cursor.fetchall()
            if scores:
                for score in scores:
                    playerList[-1]["scores"].append({"weight": score['Grams'], "cost": score['Cost'], "score": score['Score'], "round": score['Round'],
                        "solverOne": getattr(score, 'SolverOne', False), "solverTwo": getattr(score, 'SolverTwo', False),
                        "solverThree": getattr(score, 'SolverThree', False), "solverFour": getattr(score, 'SolverFour', False), 
                        "architecture": score['Architecture']})

        return jsonify({"success": True, "results": playerList})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})
    finally:
        if (cursor != None):
            cursor.close()
        if (db != None):
            db.close()
    
# get quantity of players that have finished the survey and quantity that are in the session
def surveysSubmitted():
    try:
        db = None
        cursor = None
        db = pymysql.connections.Connection(host=VT_MYSQL_HOST, user=VT_MYSQL_USER, password=VT_MYSQL_PASSWORD, database=VT_MYSQL_STSELAB_DB, port=VT_MYSQL_PORT)
        
        # First check that required data is in request, must have valid sessionId
        data = request.json
        sessionId = data.get('sessionId')

        # Create cursot to perform SQL operations on VTMySQL DB
        cursor = db.cursor(pymysql.cursors.DictCursor)
        
        # Check that players exist with matching sessionId
        sqlString = f"SELECT * FROM PlayerBrief WHERE SessionId = '{sessionId}'"
        cursor.execute(sqlString)
        players = cursor.fetchall()
        if not players:
            return jsonify({"error": "Players not found"})
        
        totalPlayers = len(players)
        surveysSubmitted = 0

        # count surveys submitted
        for player in players:
            sqlString = f"SELECT * FROM FreeRoamSurvey WHERE PlayerId = '{player['Id']}'"
            cursor.execute(sqlString)
            completedSurvey = cursor.fetchone()
            if completedSurvey:
                surveysSubmitted += 1

        return jsonify({"success": True, "totalPlayers": totalPlayers, "surveysSubmitted": surveysSubmitted})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})
    finally:
        if (cursor != None):
            cursor.close()
        if (db != None):
            db.close()