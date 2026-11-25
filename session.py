# Contains endpoints for session actions

from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
from flask import (request, jsonify)
import pymysql
import pymysql.cursors
from database import get_game_connection


def _playerRecords(cursor, players, table, condition="", parameters=(), presenceOnly=False):
    """Fetch related rows once and group them by player; SQL fragments are internal constants."""
    playerIds = tuple(str(player['Id']) for player in players)
    if not playerIds:
        return {}
    placeholders = ', '.join(['%s'] * len(playerIds))
    columns = 'DISTINCT p.Id AS RecordPlayerId' if presenceOnly else 'r.*, p.Id AS RecordPlayerId'
    # Use the roster's ID spelling even with case-insensitive database comparisons.
    sqlString = (f"SELECT {columns} FROM {table} AS r "
                 f"INNER JOIN PlayerBrief AS p ON p.Id = r.PlayerId "
                 f"WHERE p.Id IN ({placeholders}){condition}")
    cursor.execute(sqlString, playerIds + parameters)
    records = {}
    for row in cursor.fetchall():
        records.setdefault(str(row['RecordPlayerId']), []).append(row)
    return records

# Status a session, getting back the round the session is on, and the start and end dates of the session.
# This will be called repeatedly by polling front-end, and so switching to websockets would reduce the work
# needed to be done by the server.
# Even though this endpoint is always polled, it only retreives round number so minimal work is required by BE here.
def sessionStatus():
    try:
        db = None
        cursor = None
        db = get_game_connection()

        # First check that required data is in request, must have valid sessionId
        data = request.json
        sessionId = data.get('sessionId')
        playerId = data.get('playerId')

        # Create cursor to perform SQL operations on VTMySQL DB
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
        try:
            if cursor is not None:
                cursor.close()
        finally:
            if db is not None:
                db.close()
    
# Simply provides a list of players in a session, for now useful in wait room to show all players without any need
# for scores. 
def playersInSession():
    try:
        db = None
        cursor = None
        db = get_game_connection()
        
        # First check that required data is in request, must have valid sessionId
        data = request.json
        sessionId = data.get('sessionId')

        # Create cursor to perform SQL operations on VTMySQL DB
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
        
        # Only presence matters, so duplicate dice records need not be transferred.
        diceByPlayer = _playerRecords(cursor, players, 'DiceResult', presenceOnly=True)

        # Save array of all players in the session
        playerList = []
        completedOnboarding = []
        for player in players:
            # Check for players that have finished the onboarding Dice game
            didCompleteOnboarding = str(player['Id']) in diceByPlayer
            if didCompleteOnboarding:
                completedOnboarding.append(str(player['Id']))
            # Save player information
            playerList.append({"id": player['Id'], "name": player['Name'], "color": player['Color'], "completedOnboarding": didCompleteOnboarding})

        return jsonify({"success": True, "players": playerList, "completedOnboarding": completedOnboarding})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})
    finally:
        try:
            if cursor is not None:
                cursor.close()
        finally:
            if db is not None:
                db.close()
    
# applies end time to session, could be used to allow players in final results page to stop polling backend, also saves end time into 
# database.
def endSession():
    try:
        db = None
        cursor = None
        db = get_game_connection()
        
        # First check that required data is in request, must have valid sessionId
        data = request.json
        sessionId = data.get('sessionId')

        # Create cursor to perform SQL operations on VTMySQL DB
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
        try:
            if cursor is not None:
                cursor.close()
        finally:
            if db is not None:
                db.close()
    
# enpoint only used once per session to skip the golf game if desired by the host
def jumpToArmMission():
    try:
        db = None
        cursor = None
        db = get_game_connection()
        
        # First check that required data is in request, must have valid sessionId
        # I have decided on using round number to determine position in the game. 
        data = request.json
        sessionId = data.get('sessionId')

        # Create cursor to perform SQL operations on VTMySQL DB
        cursor = db.cursor(pymysql.cursors.DictCursor)

        # Ensure session exists
        sqlString = f"SELECT * FROM Session WHERE JoinCode = '{sessionId}'"
        cursor.execute(sqlString)
        session = cursor.fetchone()
        if session is None:
            return jsonify({"error": "Session not found"})
        
        mechanicalArmStartingRoundNumber = 11 # IMPORTANT!! Update this if the round number ever changes on the FE
        sqlString = f"UPDATE Session SET Round = '{mechanicalArmStartingRoundNumber}' WHERE JoinCode = '{sessionId}'"
        cursor.execute(sqlString)
        db.commit()

        return jsonify({"success": True, "round": session['Round'] + 1})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})
    finally:
        try:
            if cursor is not None:
                cursor.close()
        finally:
            if db is not None:
                db.close()
    
# Moves session to the next round, only host can call this
# Will update the round number, and the EndDate if the last round has been played
def advanceSession():
    try:
        db = None
        cursor = None
        db = get_game_connection()
        
        # First check that required data is in request, must have valid sessionId
        # I have decided on using round number to determine position in the game. 
        data = request.json
        sessionId = data.get('sessionId')

        # Create cursor to perform SQL operations on VTMySQL DB
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
        try:
            if cursor is not None:
                cursor.close()
        finally:
            if db is not None:
                db.close()
    
# Endpoint to get results for for a round rather than shoving results into session status
def roundResults():
    try:
        db = None
        cursor = None
        db = get_game_connection()
        
        # First check that required data is in request, must have valid sessionId
        data = request.json
        sessionId = data.get('sessionId')
        round = data.get('round')

        # Create cursor to perform SQL operations on VTMySQL DB
        cursor = db.cursor(pymysql.cursors.DictCursor)
        
        # Check that players exist with matching sessionId
        sqlString = f"SELECT * FROM PlayerBrief WHERE SessionId = '{sessionId}'"
        cursor.execute(sqlString)
        players = cursor.fetchall()
        if not players:
            return jsonify({"error": "Players not found"})
        
        scoresByPlayer = _playerRecords(cursor, players, 'RoundResult',
                                       ' AND r.Round = %s ORDER BY r.Id', (str(round),))

        # Save array of all players in the session, including those without a score.
        playerList = []
        for player in players:
            playerList.append({"id": player['Id'], "name": player['Name'], "color": player['Color']})
            # Keep one matching result per player, as the old fetchone() did.
            scores = scoresByPlayer.get(str(player['Id']), [])
            score = scores[0] if scores else None
            if score:
                playerList[-1]["shots"] = score['Shots']
                playerList[-1]["cost"] = score['Cost']
                playerList[-1]["solverOne"] = score.get('SolverOne', None)
                playerList[-1]["solverTwo"] = score.get('SolverTwo', None)
                playerList[-1]["solverThree"] = score.get('SolverThree', None)
                playerList[-1]["architecture"] = score['Architecture']
                playerList[-1]["score"] = score['Score']
                playerList[-1]["customPerformanceWeight"] = score.get('CustomPerformanceWeight', None)

        return jsonify({"success": True, "results": playerList})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})
    finally:
        try:
            if cursor is not None:
                cursor.close()
        finally:
            if db is not None:
                db.close()
    
# Get aggregate results of all tournament rounds
def finalResults():
    try:
        db = None
        cursor = None
        db = get_game_connection()
        
        # First check that required data is in request, must have valid sessionId
        data = request.json
        sessionId = data.get('sessionId')

        # Create cursor to perform SQL operations on VTMySQL DB
        cursor = db.cursor(pymysql.cursors.DictCursor)
        
        # Check that players exist with matching sessionId
        sqlString = f"SELECT * FROM PlayerBrief WHERE SessionId = '{sessionId}'"
        cursor.execute(sqlString)
        players = cursor.fetchall()
        if not players:
            return jsonify({"error": "Players not found"})
        
        scoresByPlayer = _playerRecords(cursor, players, 'RoundResult',
                                       ' AND r.Round > %s ORDER BY r.Id', (5,))

        # Save array of all players in the session
        playerList = []
        for player in players:
            playerList.append({"id": player['Id'], "name": player['Name'], "color": player['Color'], "scores": []})
            # For each player, also save their scores
            scores = scoresByPlayer.get(str(player['Id']), [])
            if scores:
                for score in scores:
                    playerList[-1]["scores"].append({
                        "shots": score['Shots'], 
                        "cost": score['Cost'], 
                        "score": score['Score'], 
                        "round": score['Round'],
                        "solverOne": score.get('SolverOne', None), 
                        "solverTwo": score.get('SolverTwo', None),
                        "solverThree": score.get('SolverThree', None), 
                        "architecture": score['Architecture']})

        return jsonify({"success": True, "results": playerList})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})
    finally:
        try:
            if cursor is not None:
                cursor.close()
        finally:
            if db is not None:
                db.close()
    

# Endpoint to get results for for a Mechanical Arm Mission round rather than shoving results into session status
def armRoundResults():
    try:
        db = None
        cursor = None
        db = get_game_connection()
        
        # First check that required data is in request, must have valid sessionId
        data = request.json
        sessionId = data.get('sessionId')
        round = data.get('round')


        # Create cursor to perform SQL operations on VTMySQL DB
        cursor = db.cursor(pymysql.cursors.DictCursor)
        
        # Check that players exist with matching sessionId
        sqlString = f"SELECT * FROM PlayerBrief WHERE SessionId = '{sessionId}'"
        cursor.execute(sqlString)
        players = cursor.fetchall()
        if not players:
            return jsonify({"error": "Players not found"})
        
        scoresByPlayer = _playerRecords(cursor, players, 'ArmRoundResult',
                                       ' AND r.Round = %s ORDER BY r.Id', (str(round),))

        # Save array of all players in the session, including those without a score.
        playerList = []
        for player in players:
            playerList.append({"id": player['Id'], "name": player['Name'], "color": player['Color']})
            # For each player, also save their scores, solvers, and architecture
            scores = scoresByPlayer.get(str(player['Id']), [])
            score = scores[0] if scores else None
            if score:
                playerList[-1]["weight"] = score['Grams']
                playerList[-1]["cost"] = score['Cost']
                playerList[-1]["solverOne"] = score.get('SolverOne', None)
                playerList[-1]["solverTwo"] = score.get('SolverTwo', None)
                playerList[-1]["solverThree"] = score.get('SolverThree', None)
                playerList[-1]["solverFour"] = score.get('SolverFour', None)
                playerList[-1]["architecture"] = score['Architecture']
                playerList[-1]["score"] = score['Score']

        return jsonify({"success": True, "results": playerList})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})
    finally:
        try:
            if cursor is not None:
                cursor.close()
        finally:
            if db is not None:
                db.close()
    
# Get aggregate results of all mechanical arm mission rounds
def armFinalResults():
    try:
        db = None
        cursor = None
        db = get_game_connection()
        
        # First check that required data is in request, must have valid sessionId
        data = request.json
        sessionId = data.get('sessionId')

        # Create cursor to perform SQL operations on VTMySQL DB
        cursor = db.cursor(pymysql.cursors.DictCursor)
        
        # Check that players exist with matching sessionId
        sqlString = f"SELECT * FROM PlayerBrief WHERE SessionId = '{sessionId}'"
        cursor.execute(sqlString)
        players = cursor.fetchall()
        if not players:
            return jsonify({"error": "Players not found"})
        
        scoresByPlayer = _playerRecords(cursor, players, 'ArmRoundResult', ' ORDER BY r.Id')

        # Save array of all players in the session
        playerList = []
        for player in players:
            playerList.append({"id": player['Id'], "name": player['Name'], "color": player['Color'], "scores": []})
            # For each player, also save their scores
            scores = scoresByPlayer.get(str(player['Id']), [])
            if scores:
                for score in scores:
                    playerList[-1]["scores"].append({
                        "weight": score['Grams'], 
                        "cost": score['Cost'], 
                        "score": score['Score'], 
                        "round": score['Round'],
                        "solverOne": score.get('SolverOne', None),
                        "solverTwo": score.get('SolverTwo', None),
                        "solverThree": score.get('SolverThree', None),
                        "solverFour": score.get('SolverFour', None),
                        "architecture": score['Architecture']})

        return jsonify({"success": True, "results": playerList})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})
    finally:
        try:
            if cursor is not None:
                cursor.close()
        finally:
            if db is not None:
                db.close()
    
# get quantity of players that have finished the survey and quantity that are in the session
def surveysSubmitted():
    try:
        db = None
        cursor = None
        db = get_game_connection()
        
        # First check that required data is in request, must have valid sessionId
        data = request.json
        sessionId = data.get('sessionId')

        # Create cursor to perform SQL operations on VTMySQL DB
        cursor = db.cursor(pymysql.cursors.DictCursor)
        
        # Check that players exist with matching sessionId
        sqlString = f"SELECT * FROM PlayerBrief WHERE SessionId = '{sessionId}'"
        cursor.execute(sqlString)
        players = cursor.fetchall()
        if not players:
            return jsonify({"error": "Players not found"})
        
        totalPlayers = len(players)
        submittedByPlayer = _playerRecords(cursor, players, 'FreeRoamSurvey',
                                          presenceOnly=True)
        surveysSubmitted = len(submittedByPlayer)

        return jsonify({"success": True, "totalPlayers": totalPlayers, "surveysSubmitted": surveysSubmitted})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})
    finally:
        try:
            if cursor is not None:
                cursor.close()
        finally:
            if db is not None:
                db.close()
