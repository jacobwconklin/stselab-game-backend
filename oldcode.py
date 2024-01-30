# Not best practice but I am temporarily placing old code here for quick refrence before deletion.
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
        cursor.execute(f"SELECT * FROM Users WHERE SessionId = ?", (str(sessionId)))
        players = cursor.fetchall()
        if not players:
            return jsonify({"error": "Players not found"})
        
        playerList = []
        for player in players:
            print(player.firstName)
            playerList.append({"id": player.Id, "firstName": player.FirstName, "color": player.Color})

        return jsonify({"success": True, "players": playerList})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}) 