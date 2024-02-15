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
            playerList.append({"id": player.Id, "name": player.Name, "color": player.Color, "scores": []})
            # For each player, also save their scores
            cursor.execute(f"SELECT * FROM RoundResult WHERE PlayerId = ?", (str(player.Id)))
            scores = cursor.fetchall()
            if scores:
                for score in scores:
                    playerList[-1]["scores"].append({"shots": score.Shots, "cost": score.Cost, "round": score.Round,
                        "solverOne": getattr(score, 'SolverOne', False), "solverTwo": getattr(score, 'SolverTwo', False),
                        "solverThree": getattr(score, 'SolverThree', False)})

        return jsonify({"success": True, "players": playerList, 
                        "session": {"startDate": session.StartDate, "endDate": session.EndDate, "round": session.Round}})
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
        if (newRoundNumber == 3):
            newRoundNumber = -2
        elif (newRoundNumber == 0):
            newRoundNumber = 3
        cursor.execute(f"UPDATE Session SET Round = ? WHERE JoinCode = ?", (str(newRoundNumber), str(sessionId)))
        conn.commit()

        return jsonify({"success": True, "round": session.Round + 1})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})