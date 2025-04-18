# Contains endpoints for user actions

import json
import pyodbc 
import random
import uuid
from dotenv import load_dotenv
load_dotenv()
from datetime import datetime
from flask import (request, jsonify)
from environmentSecrets import VT_MYSQL_HOST, VT_MYSQL_STSELAB_DB, VT_MYSQL_USER, VT_MYSQL_PASSWORD, VT_MYSQL_PORT, VT_MYSQL_PASSWORD_SALT
import pymysql
import pymysql.cursors

# Begins a new game by a host, creating a session. Will need all of the information collected for each player, without
# a join code. Must return if successful or not, and if successful, the join code for the session.
# @app.route('/player/host', methods=['POST'])
def host():
    try:
        db = None
        cursor = None
        db = pymysql.connections.Connection(host=VT_MYSQL_HOST, user=VT_MYSQL_USER, password=VT_MYSQL_PASSWORD, database=VT_MYSQL_STSELAB_DB, port=VT_MYSQL_PORT)
        
        # First pull data from request
        data = request.json
        name = data.get('name')
        color = data.get('color')
        participationReason = data.get('participationReason')
        gender = data.get('gender')
        age = data.get('age')

        residence = data.get('residence')
        ethnicity = data.get('ethnicity')

        isCollegeStudent = data.get('isCollegeStudent')
        if isCollegeStudent:
            isCollegeStudent = 1
        else:
            isCollegeStudent = 0
        university = data.get('university')
        degreeProgram = data.get('degreeProgram')
        yearsInProgram = data.get('yearsInProgram')
        highSchoolEducation = data.get('highSchoolEducation')
        bachelorsEducation = data.get('bachelorsEducation')
        mastersEducation = data.get('mastersEducation')
        doctorateEducation = data.get('doctorateEducation')
        otherEducation = data.get('otherEducation')
        otherEducationName = data.get('otherEducationName')

        riskAnalysisExperience = data.get('riskAnalysisExperience')
        supplierExperience = data.get('supplierExperience')
        proposalOrStatementOfWorkExperience = data.get('proposalOrStatementOfWorkExperience')
        bidsForRequestsExperience = data.get('bidsForRequestsExperience')
        systemArchitectureExperience = data.get('systemArchitectureExperience')
        golfExperience = data.get('golfExperience')

        systemsEngineeringExpertise = data.get('systemsEngineeringExpertise')
        statementOfWorkExpertise = data.get('statementOfWorkExpertise')

        
        # return error if required params aren't present
        if name is None or color is None:
            return jsonify({"error": "Missing required parameters"})

        # Create cursor to perform SQL operations on VTMySQL DB
        cursor = db.cursor(pymysql.cursors.DictCursor)

        # Now generate a join code and create a new session in the database
        joinCode = random.randint(100000, 999999)
        # check join code doesn't already exist in database
        newCode = False
        while not newCode:
            sqlString = f"SELECT * FROM Session WHERE JoinCode = '{str(joinCode)}'"
            cursor.execute(sqlString)
            retreived = cursor.fetchone()
            if retreived is None:
                newCode = True
            else:
                joinCode = random.randint(100000, 999999)

        # Insert new session into database
        # Now using UTC date, previously used: datetime.today().strftime('%Y-%m-%d %H:%M:%S') as a varchar
        sqlString = f"INSERT INTO Session (JoinCode, Round, StartDate, EndDate) VALUES ('{str(joinCode)}', 0, CURRENT_TIMESTAMP(), {'NULL'})"
        cursor.execute(sqlString)
        db.commit()

        # Generate UUID for player
        playerId = uuid.uuid4()

        # Create brief version of Player to be retrieved during the game polling
        sqlString = f"INSERT INTO PlayerBrief (Id, Name, Color, SessionId) VALUES ('{str(playerId)}', '{name}', '{color}', '{str(joinCode)}')"
        cursor.execute(sqlString)
        db.commit()

        # Now create new extensive Player Information and save all information in the db with the same id
        sqlString = f'''INSERT INTO PlayerInformation (Id, Name, ParticipationReason, Gender, Age, Residence, Ethnicity, IsCollegeStudent, University, DegreeProgram, YearsInProgram, HighSchoolEducation, BachelorsEducation, MastersEducation, DoctorateEducation, OtherEducation, OtherEducationName, RiskAnalysisExperience, SupplierExperience, ProposalOrStatementOfWorkExperience, BidsForRequestsExperience, SystemArchitectureExperience, GolfExperience, SystemsEngineeringExpertise, StatementOfWorkExpertise) Values ('{str(playerId)}', '{name}', '{participationReason}', '{gender}', '{age}', '{residence}', '{ethnicity}', {isCollegeStudent}, '{university}', '{degreeProgram}', '{yearsInProgram}', '{highSchoolEducation}', '{bachelorsEducation}', '{mastersEducation}', '{doctorateEducation}', '{otherEducation}', '{otherEducationName}', '{riskAnalysisExperience}', '{supplierExperience}', '{proposalOrStatementOfWorkExperience}', '{bidsForRequestsExperience}', '{systemArchitectureExperience}', '{golfExperience}', '{systemsEngineeringExpertise}', '{statementOfWorkExpertise}')'''

        cursor.execute(sqlString)  
        db.commit()

        # On success return success and join code
        return jsonify({"success": True, "joinCode": joinCode, "playerId": playerId})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})
    finally:
        if (cursor != None):
            cursor.close()
        if (db != None):
            db.close()
    

# Joins a game creating a player for a given session IF that session exists
def join():
    try:
        db = None
        cursor = None
        db = pymysql.connections.Connection(host=VT_MYSQL_HOST, user=VT_MYSQL_USER, password=VT_MYSQL_PASSWORD, database=VT_MYSQL_STSELAB_DB, port=VT_MYSQL_PORT)
        
        # First pull data request, must have valid join code
        data = request.json
        name = data.get('name')
        color = data.get('color')
        participationReason = data.get('participationReason')
        gender = data.get('gender')
        age = data.get('age')

        residence = data.get('residence')
        ethnicity = data.get('ethnicity')

        isCollegeStudent = data.get('isCollegeStudent')
        if isCollegeStudent:
            isCollegeStudent = 1
        else:
            isCollegeStudent = 0
        university = data.get('university')
        degreeProgram = data.get('degreeProgram')
        yearsInProgram = data.get('yearsInProgram')
        highSchoolEducation = data.get('highSchoolEducation')
        bachelorsEducation = data.get('bachelorsEducation')
        mastersEducation = data.get('mastersEducation')
        doctorateEducation = data.get('doctorateEducation')
        otherEducation = data.get('otherEducation')
        otherEducationName = data.get('otherEducationName')

        riskAnalysisExperience = data.get('riskAnalysisExperience')
        supplierExperience = data.get('supplierExperience')
        proposalOrStatementOfWorkExperience = data.get('proposalOrStatementOfWorkExperience')
        bidsForRequestsExperience = data.get('bidsForRequestsExperience')
        systemArchitectureExperience = data.get('systemArchitectureExperience')
        golfExperience = data.get('golfExperience')

        systemsEngineeringExpertise = data.get('systemsEngineeringExpertise')
        statementOfWorkExpertise = data.get('statementOfWorkExpertise')
        
        joinCode = data.get('joinCode')

        # return error if required params aren't present
        if name is None or color is None or joinCode is None:
            return jsonify({"error": "Missing required parameters"})

        # Create cursor to perform SQL operations on VTMySQL DB
        cursor = db.cursor(pymysql.cursors.DictCursor)

        # Check that session exists
        sqlString = f"SELECT * FROM Session WHERE JoinCode = '{str(joinCode)}'"
        cursor.execute(sqlString)
        session = cursor.fetchone()
        if session is None:
            return jsonify({"error": "Session not found"})
        
        # Below code would check that session hasn't already started (Should still be on round 0)
        # Currently allow players to join 'late' to a started session, just comment out the code below to prevent that:
        # if session.Round != 0:
        #     return jsonify({"error": "Session has already started"})

        # Generate UUID for player
        playerId = uuid.uuid4()

        # Now create new brief version of the player and insert them into the database
        sqlString = f"INSERT INTO PlayerBrief (Id, Name, Color, SessionId) VALUES ('{str(playerId)}', '{name}', '{color}', '{str(joinCode)}')"
        cursor.execute(sqlString)  
        db.commit()

        # Now save extensive player information into the database
        # Now create new extensive Player Information and save all information in the db with the same id
        sqlString = f'''INSERT INTO PlayerInformation (Id, Name, ParticipationReason, Gender, Age, Residence, Ethnicity, IsCollegeStudent, University, DegreeProgram, YearsInProgram, HighSchoolEducation, BachelorsEducation, MastersEducation, DoctorateEducation, OtherEducation, OtherEducationName, RiskAnalysisExperience, SupplierExperience, ProposalOrStatementOfWorkExperience, BidsForRequestsExperience, SystemArchitectureExperience, GolfExperience, SystemsEngineeringExpertise, StatementOfWorkExpertise) Values ('{str(playerId)}', '{name}', '{participationReason}', '{gender}', '{age}', '{residence}', '{ethnicity}', {isCollegeStudent}, '{university}', '{degreeProgram}', '{yearsInProgram}', '{highSchoolEducation}', '{bachelorsEducation}', '{mastersEducation}', '{doctorateEducation}', '{otherEducation}', '{otherEducationName}', '{riskAnalysisExperience}', '{supplierExperience}', '{proposalOrStatementOfWorkExperience}', '{bidsForRequestsExperience}', '{systemArchitectureExperience}', '{golfExperience}', '{systemsEngineeringExpertise}', '{statementOfWorkExpertise}')'''

        cursor.execute(sqlString)  
        db.commit()

        return jsonify({"success": True, "playerId": playerId})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})
    finally:
        if (cursor != None):
            cursor.close()
        if (db != None):
            db.close()
    

# Removes a player from a session, called by the host to remove them or the player themselves to leave
# Will start with just changing session id so data remains in db for aggregate results (as they only appear after reaching tournament stages)
# but can be changed to remove player data from the database (and all reliant round results in recursive delete) if desired.
def remove():
    try:
        db = None
        cursor = None
        db = pymysql.connections.Connection(host=VT_MYSQL_HOST, user=VT_MYSQL_USER, password=VT_MYSQL_PASSWORD, database=VT_MYSQL_STSELAB_DB, port=VT_MYSQL_PORT)
        
        # First check that required data is in request, must have valid playerId
        data = request.json
        playerId = data.get('playerId')

        # Create cursor to perform SQL operations on VTMySQL DB
        cursor = db.cursor(pymysql.cursors.DictCursor)

        # Ensure player exists
        sqlString = f"SELECT * FROM PlayerBrief WHERE Id = '{str(playerId)}'"
        cursor.execute(sqlString)
        player = cursor.fetchone()
        if player is None:
            return jsonify({"error": "Player not found"})
        
        sqlString = f"UPDATE PlayerBrief SET SessionId = NULL WHERE Id = '{str(playerId)}'"
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


# Saves the result for one player for one round of the tournament. Includes shots, cost, and solvers played with
def roundResult():
    try:
        db = None
        cursor = None
        db = pymysql.connections.Connection(host=VT_MYSQL_HOST, user=VT_MYSQL_USER, password=VT_MYSQL_PASSWORD, database=VT_MYSQL_STSELAB_DB, port=VT_MYSQL_PORT)
        
        # Save player's results for a round in the tournament
        # First check that required data is in request, must have valid Id for Player,
        # as well as shot, cost, and round information
        data = request.json
        id = data.get('playerId')
        shots = data.get('shots')
        cost = data.get('cost')
        solverOne = data.get('solverOne')
        if solverOne is None:
            solverOne = "NULL"
        solverTwo = data.get('solverTwo')
        if solverTwo is None:
            solverTwo = "NULL"
        solverThree = data.get('solverThree')
        if solverThree is None:
            solverThree = "NULL"
        architecture = data.get('architecture')
        round = data.get('round')
        score = data.get('score')
        customPerformanceWeight = data.get('customPerformanceWeight')
        reasoning = data.get('reasoning')

        # if score is none save it as -1
        if score is None:
            score = -1

        # Create cursor to perform SQL operations on VTMySQL DB
        cursor = db.cursor(pymysql.cursors.DictCursor)

        # Check that player exists
        sqlString = f"SELECT * FROM PlayerBrief WHERE Id = '{str(id)}'"
        cursor.execute(sqlString)
        player = cursor.fetchone()
        if player is None:
            return jsonify({"error": "Player not found"})
        
        # solver types: quantity is dependent on round number, there may be 1 (rounds 1 and 2), 
        # 2 (round 3), or 3 (round 4)
        # So space is reserved for 3 solvers for each round result but value may be None / Null

        # Now create new Round Result and insert into its table
        sqlString = f"INSERT INTO RoundResult (Round, Shots, Cost, SolverOne, SolverTwo, SolverThree, PlayerId, Architecture, Score, CustomPerformanceWeight, Reasoning) VALUES ('{str(round)}', '{str(shots)}', '{str(cost)}', {solverOne}, {solverTwo}, {solverThree}, '{str(id)}', '{architecture}', '{str(score)}', '{customPerformanceWeight}', '{str(reasoning)}')"
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
    
# Saves the result for one player for one round of the Mechanical Arm Mission. Includes Grams(weight), cost, architecture, score, and solvers played with
def armRoundResult():
    try:
        db = None
        cursor = None
        db = pymysql.connections.Connection(host=VT_MYSQL_HOST, user=VT_MYSQL_USER, password=VT_MYSQL_PASSWORD, database=VT_MYSQL_STSELAB_DB, port=VT_MYSQL_PORT)
        
        # Save player's results for a round in the Mechanical Arm Mission
        # First check that required data is in request, must have valid Id for Player,
        # as well as weight, cost, and round information
        data = request.json
        id = data.get('playerId')
        weight = data.get('weight')
        cost = data.get('cost')
        solverOne = data.get('solverOne')
        solverTwo = data.get('solverTwo')
        solverThree = data.get('solverThree')
        solverFour = data.get('solverFour')
        
        solverOne = data.get('solverOne')
        if solverOne is None:
            solverOne = "NULL"
        solverTwo = data.get('solverTwo')
        if solverTwo is None:
            solverTwo = "NULL"
        solverThree = data.get('solverThree')
        if solverThree is None:
            solverThree = "NULL"
        if solverFour is None:
            solverFour = "NULL"

        architecture = data.get('architecture')
        round = data.get('round')
        score = data.get('score')
        # if score is none save it as -1
        if score is None:
            score = -1

        # Create cursor to perform SQL operations on VTMySQL DB
        cursor = db.cursor(pymysql.cursors.DictCursor)

        # Check that player exists
        sqlString = f"SELECT * FROM PlayerBrief WHERE Id = '{str(id)}'"
        cursor.execute(sqlString)
        player = cursor.fetchone()
        if player is None:
            return jsonify({"error": "Player not found"})
        
        # solver types: quantity is dependent on round number, there may be 1 - 4
        # So space is reserved for 4 solvers for each round result but value may be None / Null

        # Now create new Round Result and insert into its table
        sqlString = f"INSERT INTO ArmRoundResult (Round, Grams, Cost, SolverOne, SolverTwo, SolverThree, SolverFour, PlayerId, Architecture, Score) VALUES ('{str(round)}', '{str(weight)}', '{str(cost)}', {solverOne}, {solverTwo}, {solverThree}, {solverFour}, '{str(id)}', '{architecture}', '{str(score)}')"
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
    
# Retreives ALL Round Results to show aggregate results across all tournaments played before. 
def allResults():
    try:
        db = None
        cursor = None
        db = pymysql.connections.Connection(host=VT_MYSQL_HOST, user=VT_MYSQL_USER, password=VT_MYSQL_PASSWORD, database=VT_MYSQL_STSELAB_DB, port=VT_MYSQL_PORT)
        
        # Create cursor to perform SQL operations on VTMySQL DB
        cursor = db.cursor(pymysql.cursors.DictCursor)

        # Get all round results from Tournament Stages
        sqlString = "SELECT * FROM RoundResult JOIN PlayerBrief ON RoundResult.PlayerId = PlayerBrief.Id WHERE Round > 5"
        cursor.execute(sqlString)
        results = cursor.fetchall()

        #  pyodbc.Row objects are not json serializable so convert and coerce any values not serializable (like decimals) into strings
        # results = [tuple(row) for row in results] # Saves as a tuple, harder to read on FE
        # json_string = json.dumps(results, default=str)
        # Note: as of 04/2024 no longer using pyodbc, but leaving this as it converts all 
        # properties to a lowercase first letter, which the FE expects.
        resultList = []
        for result in results:
            resultList.append({"id": result['Id'], "name": result['Name'], "color": result['Color'], "score": result['Score'], "round": result['Round'], "shots": result['Shots'], "cost": result['Cost'], "solverOne": result['SolverOne'], "solverTwo": result['SolverTwo'], "solverThree": result['SolverThree'], "architecture": result['Architecture'], "customPerformanceWeight": result['CustomPerformanceWeight']})

        # Now return all results
        return  jsonify({"results": resultList})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})
    finally:
        if (cursor != None):
            cursor.close()
        if (db != None):
            db.close()
    
# Saves the result of a player playing free roam modules in the playground. includes shots, distance remaining to hole (up to 2 decimal places), solver used, and module selected, as well as the player's id 
def freeRoamResult():
    try:
        db = None
        cursor = None
        db = pymysql.connections.Connection(host=VT_MYSQL_HOST, user=VT_MYSQL_USER, password=VT_MYSQL_PASSWORD, database=VT_MYSQL_STSELAB_DB, port=VT_MYSQL_PORT)
        
        # Save player's results for a round in the tournament
        # First check that required data is in request, must have valid Id for Player,
        # as well as shot, cost, and round information
        data = request.json
        id = data.get('playerId')
        shots = data.get('shots')
        distance = data.get('distance')
        solver = data.get('solver')
        module = data.get('module')

        # Create cursor to perform SQL operations on VTMySQL DB
        cursor = db.cursor(pymysql.cursors.DictCursor)

        # Check that player exists
        sqlString = f"SELECT * FROM PlayerBrief WHERE Id = '{str(id)}'"
        cursor.execute(sqlString)
        player = cursor.fetchone()
        if player is None:
            return jsonify({"error": "Player not found"})

        # Now create new Free Roam Result and insert into its table
        sqlString = f"INSERT INTO FreeRoamResult (Shots, Distance, Solver, Module, PlayerId, TimeStamp) VALUES ('{str(shots)}', '{str(distance)}', '{solver}', '{module}', '{str(id)}', CURRENT_TIMESTAMP())"
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
    
# Saves the result of a player Free roam survey 
# The number stored per module is for a solver as an int that can represent multiple solvers as follows:
# 0 -> None = Not Sure
# 1 -> Professional
# 2 -> Amateur
# 3 -> Specialist
# 4 -> Professional and Amateur
# 5 -> Professional and Specialist
# 6 -> Amateur and Specialist
# 7 -> Professional, Amateur, and Specialist (could be stored without not sure option in 3 bits!)
def freeRoamSurvey():
    try:
        db = None
        cursor = None
        db = pymysql.connections.Connection(host=VT_MYSQL_HOST, user=VT_MYSQL_USER, password=VT_MYSQL_PASSWORD, database=VT_MYSQL_STSELAB_DB, port=VT_MYSQL_PORT)
        
        # Save player's results for a round in the tournament
        # First check that required data is in request, must have valid Id for Player,
        # as well as shot, cost, and round information
        data = request.json
        id = data.get('playerId')
        drive = data.get('drive')
        long = data.get('long')
        fairway = data.get('fairway')
        short = data.get('short')
        putt = data.get('putt')
        entireHole = data.get('entireHole')

        # Create cursor to perform SQL operations on VTMySQL DB
        cursor = db.cursor(pymysql.cursors.DictCursor)

        # Check that player exists
        sqlString = f"SELECT * FROM PlayerBrief WHERE Id = '{str(id)}'"
        cursor.execute(sqlString)
        player = cursor.fetchone()
        if player is None:
            return jsonify({"error": "Player not found"})

        # Now create new Free Roam Result and insert into its table
        sqlString = f"INSERT INTO FreeRoamSurvey (Drive, LongChoice, Fairway, Short, Putt, EntireHole, PlayerId) VALUES ('{str(drive)}', '{str(long)}', '{str(fairway)}', '{str(short)}', '{str(putt)}', '{str(entireHole)}', '{str(id)}')"
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
    

# Save result of player playing onboarding or offboarding dice game
def diceResult():
    try:
        db = None
        cursor = None
        db = pymysql.connections.Connection(host=VT_MYSQL_HOST, user=VT_MYSQL_USER, password=VT_MYSQL_PASSWORD, database=VT_MYSQL_STSELAB_DB, port=VT_MYSQL_PORT)
        
        # First check that required data is in request, must have valid Id for Player,
        # as well as required Die, whether it is onboarding, and the score.
        data = request.json
        id = data.get('playerId')
        score = data.get('score')
        onboarding = data.get('onboarding')
        if onboarding:
            onboarding = 1
        else:
            onboarding = 0
        d6 = data.get('d6')
        d8 = data.get('d8')
        d10 = data.get('d10')
        d12 = data.get('d12')
        d20 = data.get('d20')
        reasoning = data.get('reasoning')
        finalReasoning = data.get('finalReasoning')
        reasoning2 = data.get('reasoning2')
        reasoning3 = data.get('reasoning3')
        reasoning4 = data.get('reasoning4')
        reasoning5 = data.get('reasoning5')

        if d6 is None:
            d6 = 0
        if d8 is None:
            d8 = 0
        if d10 is None:
            d10 = 0
        if d12 is None:
            d12 = 0
        if d20 is None:
            d20 = 0

        # D6 int,
        # D8 int,
        # D10 int, 
        # D12 int,
        # D20 int,
        # PlayerId varchar(255) FOREIGN KEY REFERENCES PlayerBrief(Id),
        # Onboarding bit,
        # Score int

        # Create cursor to perform SQL operations on VTMySQL DB
        cursor = db.cursor(pymysql.cursors.DictCursor)

        # Check that player exists
        sqlString = f"SELECT * FROM PlayerBrief WHERE Id = '{str(id)}'"
        cursor.execute(sqlString)
        player = cursor.fetchone()
        if player is None:
            return jsonify({"error": "Player not found"})

        # Now create new DiceResult and insert into its table
        sqlString = f"INSERT INTO DiceResult (D6, D8, D10, D12, D20, PlayerId, Onboarding, Score, Reasoning, FinalReasoning, Reasoning2, Reasoning3, Reasoning4, Reasoning5) VALUES ('{str(d6)}', '{str(d8)}', '{str(d10)}', '{str(d12)}', '{str(d20)}', '{str(id)}', {onboarding}, '{str(score)}', '{str(reasoning)}', '{str(finalReasoning)}','{str(reasoning2)}','{str(reasoning3)}', '{str(reasoning4)}','{str(reasoning5)}')"
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