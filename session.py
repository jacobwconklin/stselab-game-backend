# Contains endpoints for session actions

import pyodbc 
from dotenv import load_dotenv
load_dotenv()
from flask import (request, jsonify)
from environmentSecrets import AZURE_SQL_CONNECTION_STRING

# Status a session, includes retreiving all players in a session and all scores for each player
# This will be called repeatedly by polling front-end, and so switching to websockets would reduce the work
# needed to be done by the server.
# TODO even if I do keep polling, I could break this down into getting session, getting all players, and getting scores, so that
# only the work of checking session round has to be done constantly. 

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
        cursor.execute(f"SELECT * FROM PlayerBrief WHERE Id = ?", (str(playerId)))
        player = cursor.fetchone()
        if player and str(player.SessionId) != str(sessionId):
            return jsonify({"error": "Player not in session"})

        # Check that players exist with matching sessionId
        cursor.execute(f"SELECT * FROM PlayerBrief WHERE SessionId = ?", (str(sessionId)))
        players = cursor.fetchall()
        if not players:
            return jsonify({"error": "Players not found"})
        
        # Save array of all players in the session
        playerList = []
        for player in players:
            playerList.append({"id": player.Id, "name": player.Name, "color": player.Color})

        return jsonify({"success": True, "players": playerList,
                        "session": {"round": session.Round}})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}) 
    
# Moves session to the next round, only host can call this
# Will update the round number, and the EndDate if the last round has been played
def advanceSession():
    try:
        # First check that required data is in request, must have valid sessionId
        # TODO could add state to Session to track non-rounds like playground, or end of tournament,
        # or could continue to have every screen be a round #.
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
        
        newRoundNumber = session.Round + 1
        cursor.execute(f"UPDATE Session SET Round = ? WHERE JoinCode = ?", (str(newRoundNumber), str(sessionId)))
        conn.commit()

        return jsonify({"success": True, "round": session.Round + 1})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})
    
# Endpoint to get results for for a round rather than shoving results into session status
def roundResults():
    try:
        # First check that required data is in request, must have valid sessionId
        data = request.json
        sessionId = data.get('sessionId')
        round = data.get('round')

        # Create connection to Azure SQL Database
        conn = pyodbc.connect(AZURE_SQL_CONNECTION_STRING, timeout=120)
        cursor = conn.cursor()
        
        # Check that players exist with matching sessionId
        cursor.execute(f"SELECT * FROM PlayerBrief WHERE SessionId = ?", (str(sessionId)))
        players = cursor.fetchall()
        if not players:
            return jsonify({"error": "Players not found"})
        
        # Save array of all players in the session
        # players = [
        #     {"id": 1, "name": "Player 1", "color": "red", "shots": 50, "cost": 100, "solverOne": 0, "solverTwo": 2, "architecture": "h" },
        # ]
        playerList = []
        for player in players:
            playerList.append({"id": player.Id, "name": player.Name, "color": player.Color})
            # For each player, also save their scores, solvers, and architecture
            cursor.execute(f"SELECT * FROM RoundResult WHERE PlayerId = ? AND Round = ?", (str(player.Id), str(round)))
            score = cursor.fetchone()
            if score:
                playerList[-1]["shots"] = score.Shots
                playerList[-1]["cost"] = score.Cost
                playerList[-1]["solverOne"] = getattr(score, 'SolverOne', None)
                playerList[-1]["solverTwo"] = getattr(score, 'SolverTwo', None)
                playerList[-1]["solverThree"] = getattr(score, 'SolverThree', None)
                playerList[-1]["architecture"] = score.Architecture

        return jsonify({"success": True, "results": playerList})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})
    
# Get aggregate results of all tournament rounds
def finalResults():
    try:
        # First check that required data is in request, must have valid sessionId
        data = request.json
        sessionId = data.get('sessionId')

        # Create connection to Azure SQL Database
        conn = pyodbc.connect(AZURE_SQL_CONNECTION_STRING, timeout=120)
        cursor = conn.cursor()
        
        # Check that players exist with matching sessionId
        cursor.execute(f"SELECT * FROM PlayerBrief WHERE SessionId = ?", (str(sessionId)))
        players = cursor.fetchall()
        if not players:
            return jsonify({"error": "Players not found"})
        
        # Save array of all players in the session
        playerList = []
        for player in players:
            playerList.append({"id": player.Id, "name": player.Name, "color": player.Color, "scores": []})
            # For each player, also save their scores
            cursor.execute(f"SELECT * FROM RoundResult WHERE PlayerId = ? AND Round > 5", (str(player.Id)))
            scores = cursor.fetchall()
            if scores:
                for score in scores:
                    playerList[-1]["scores"].append({"shots": score.Shots, "cost": score.Cost, "round": score.Round,
                        "solverOne": getattr(score, 'SolverOne', False), "solverTwo": getattr(score, 'SolverTwo', False),
                        "solverThree": getattr(score, 'SolverThree', False), "architecture": score.Architecture})

        return jsonify({"success": True, "results": playerList})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})