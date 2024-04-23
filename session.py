# Contains endpoints for session actions

from datetime import datetime
import pyodbc 
from dotenv import load_dotenv
load_dotenv()
from flask import (request, jsonify)
from environmentSecrets import AZURE_SQL_CONNECTION_STRING

# Status a session, getting back the round the session is on only.
# TODO may want to send start and end time if relevant
# This will be called repeatedly by polling front-end, and so switching to websockets would reduce the work
# needed to be done by the server.
# Even though this endpoint is always polled, it only retreives round number so minimal work is required by BE here.
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

        return jsonify({"success": True, "session": {"round": session.Round, "startDate": session.StartDate, "endDate": session.EndDate}})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}) 
    
# Simply provides a list of players in a session, for now useful in wait room to show all players without any need
# for scores. 
def playersInSession():
    try:
        # First check that required data is in request, must have valid sessionId
        data = request.json
        sessionId = data.get('sessionId')

        # Create connection to Azure SQL Database
        conn = pyodbc.connect(AZURE_SQL_CONNECTION_STRING, timeout=120)
        cursor = conn.cursor()

        # Save information about session itself
        cursor.execute(f"SELECT * FROM Session WHERE JoinCode = ?", (str(sessionId)))
        session = cursor.fetchone()
        if session is None:
            return jsonify({"error": "Session not found"})

        # Check that players exist with matching sessionId
        cursor.execute(f"SELECT * FROM PlayerBrief WHERE SessionId = ?", (str(sessionId)))
        players = cursor.fetchall()
        if not players:
            return jsonify({"error": "Players not found"})
        
        # Save array of all players in the session
        playerList = []
        completedOnboarding = []
        for player in players:
            # Check for players that have finished the onboarding Dice game
            cursor.execute(f"SELECT * FROM DiceResult WHERE PlayerId = ?", (str(player.Id)))
            diceResult = cursor.fetchone()
            didCompleteOnboarding = False
            if diceResult:
                completedOnboarding.append(str(player.Id))
                didCompleteOnboarding = True
            # Save player information
            playerList.append({"id": player.Id, "name": player.Name, "color": player.Color, "completedOnboarding": didCompleteOnboarding})

        return jsonify({"success": True, "players": playerList, "completedOnboarding": completedOnboarding})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})
    
# applies end time to session, could be used to allow players in final results page to stop polling backend, also saves end time into 
# database.
def endSession():
    try:
        # First check that required data is in request, must have valid sessionId
        data = request.json
        sessionId = data.get('sessionId')

        # Create connection to Azure SQL Database
        conn = pyodbc.connect(AZURE_SQL_CONNECTION_STRING, timeout=120)
        cursor = conn.cursor()

        # Save information about session itself
        cursor.execute(f"SELECT * FROM Session WHERE JoinCode = ?", (str(sessionId)))
        session = cursor.fetchone()
        if session is None:
            return jsonify({"error": "Session not found"})
        
        # Update the end date of the session
        # TODO to use UTC date just put GETUTCDATE() in the query
        newEndDate = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(f"UPDATE Session SET EndDate = ? WHERE JoinCode = ?", 
            (newEndDate, str(sessionId)))
        conn.commit()
        return jsonify({"success": True, "endDate": newEndDate})
    except Exception as e:
            print(e)
            return jsonify({"error": str(e)})
    
    
# Moves session to the next round, only host can call this
# Will update the round number, and the EndDate if the last round has been played
def advanceSession():
    try:
        # First check that required data is in request, must have valid sessionId
        # I have decided on using round number to determine position in the game. 
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
                playerList[-1]["score"] = score.Score
                playerList[-1]["customPerformanceWeight"] = getattr(score, 'CustomPerformanceWeight', None)

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
                    playerList[-1]["scores"].append({"shots": score.Shots, "cost": score.Cost, "score": score.Score, "round": score.Round,
                        "solverOne": getattr(score, 'SolverOne', False), "solverTwo": getattr(score, 'SolverTwo', False),
                        "solverThree": getattr(score, 'SolverThree', False), "architecture": score.Architecture})

        return jsonify({"success": True, "results": playerList})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})
    

# Endpoint to get results for for a Mechanical Arm Mission round rather than shoving results into session status
def armRoundResults():
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
        #     {"id": 1, "name": "Player 1", "color": "red", "weight": 50, "cost": 100, "solverOne": 0, "solverTwo": 2, "architecture": "Manipulator and Grabber" },
        # ]
        playerList = []
        for player in players:
            playerList.append({"id": player.Id, "name": player.Name, "color": player.Color})
            # For each player, also save their scores, solvers, and architecture
            cursor.execute(f"SELECT * FROM ArmRoundResult WHERE PlayerId = ? AND Round = ?", (str(player.Id), str(round)))
            score = cursor.fetchone()
            if score:
                playerList[-1]["weight"] = score.Grams
                playerList[-1]["cost"] = score.Cost
                playerList[-1]["solverOne"] = getattr(score, 'SolverOne', None)
                playerList[-1]["solverTwo"] = getattr(score, 'SolverTwo', None)
                playerList[-1]["solverThree"] = getattr(score, 'SolverThree', None)
                playerList[-1]["solverFour"] = getattr(score, 'SolverFour', None)
                playerList[-1]["architecture"] = score.Architecture
                playerList[-1]["score"] = score.Score

        return jsonify({"success": True, "results": playerList})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})
    
# Get aggregate results of all mechanical arm mission rounds
def armFinalResults():
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
            cursor.execute(f"SELECT * FROM ArmRoundResult WHERE PlayerId = ?", (str(player.Id)))
            scores = cursor.fetchall()
            if scores:
                for score in scores:
                    playerList[-1]["scores"].append({"weight": score.Grams, "cost": score.Cost, "score": score.Score, "round": score.Round,
                        "solverOne": getattr(score, 'SolverOne', False), "solverTwo": getattr(score, 'SolverTwo', False),
                        "solverThree": getattr(score, 'SolverThree', False), "solverFour": getattr(score, 'SolverFour', False), 
                        "architecture": score.Architecture})

        return jsonify({"success": True, "results": playerList})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})



















    
# get quantity of players that have finished the survey and quantity that are in the session
def surveysSubmitted():
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
        
        totalPlayers = len(players)
        surveysSubmitted = 0

        # count surveys submitted
        for player in players:
            cursor.execute(f"SELECT * FROM FreeRoamSurvey WHERE PlayerId = ?", (str(player.Id)))
            completedSurvey = cursor.fetchone()
            if completedSurvey:
                surveysSubmitted += 1

        return jsonify({"success": True, "totalPlayers": totalPlayers, "surveysSubmitted": surveysSubmitted})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})