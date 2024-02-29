# Contains endpoints for user actions

import json
import pyodbc 
import random
import uuid
from dotenv import load_dotenv
load_dotenv()
from datetime import datetime
from flask import (request, jsonify)
from environmentSecrets import AZURE_SQL_CONNECTION_STRING

# Begins a new game by a host, creating a session. Will need all of the information collected for each player, without
# a join code. Must return if successful or not, and if successful, the join code for the session.
# @app.route('/player/host', methods=['POST'])
def host():
    try:
        # First pull data from request
        data = request.json
        name = data.get('name')
        color = data.get('color')
        participationReason = data.get('participationReason')
        gender = data.get('gender')
        age = data.get('age')
        country = data.get('country')
        hobbies = data.get('hobbies')
        isCollegeStudent = data.get('isCollegeStudent')
        university = data.get('university')
        degreeProgram = data.get('degreeProgram')
        yearsInProgram = data.get('yearsInProgram')
        highSchoolEducation = data.get('highSchoolEducation')
        associatesEducation = data.get('associatesEducation')
        bachelorsEducation = data.get('bachelorsEducation')
        mastersEducation = data.get('mastersEducation')
        professionalEducation = data.get('professionalEducation')
        doctorateEducation = data.get('doctorateEducation')
        otherEducation = data.get('otherEducation')
        otherEducationName = data.get('otherEducationName')
        aerospaceEngineeringSpecialization = data.get('aerospaceEngineeringSpecialization')
        designSpecialization = data.get('designSpecialization')
        electricalEngineeringSpecialization = data.get('electricalEngineeringSpecialization')
        industrialEngineeringSpecialization = data.get('industrialEngineeringSpecialization')
        manufacturingSpecialization = data.get('manufacturingSpecialization')
        materialScienceSpecialization = data.get('materialScienceSpecialization')
        mechanicalEngineeringSpecialization = data.get('mechanicalEngineeringSpecialization')
        projectManagementSpecialization = data.get('projectManagementSpecialization')
        roboticsSpecialization = data.get('roboticsSpecialization')
        softwareSpecialization = data.get('softwareSpecialization')
        systemsEngineeringSpecialization = data.get('systemsEngineeringSpecialization')
        otherSpecialization = data.get('otherSpecialization')
        otherSpecializationName = data.get('otherSpecializationName')
        systemsEngineeringExpertise = data.get('systemsEngineeringExpertise')
        statementOfWorkExpertise = data.get('statementOfWorkExpertise')

        # TODO return error if there are not required params

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

        # Create brief version of Player to be retrieved during the game polling
        cursor.execute(f"INSERT INTO PlayerBrief (Id, Name, Color, SessionId) VALUES (?, ?, ?, ?)",
            (playerId, name, color, str(joinCode)))
        conn.commit()

        # Now create new extensive Player Information and save all information in the db with the same id
        cursor.execute(f'''INSERT INTO PlayerInformation (Id, Name, ParticipationReason, Gender, Age, Country, 
                       Hobbies, IsCollegeStudent, University, DegreeProgram, YearsInProgram, HighSchoolEducation, 
                       AssociatesEducation, BachelorsEducation, MastersEducation, ProfessionalEducation, 
                       DoctorateEducation, OtherEducation, OtherEducationName, AerospaceEngineeringSpecialization,
                       DesignSpecialization, ElectricalEngineeringSpecialization, IndustrialEngineeringSpecialization,
                       ManufacturingSpecialization, MaterialScienceSpecialization, MechanicalEngineeringSpecialization,
                       ProjectManagementSpecialization, RoboticsSpecialization, 
                       SoftwareSpecialization, SystemsEngineeringSpecialization, OtherSpecialization, OtherSpecializationName,
                       SystemsEngineeringExpertise, StatementOfWorkExpertise) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                       ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
            (playerId, name, participationReason, gender, age, country, hobbies, isCollegeStudent, university, degreeProgram,
             yearsInProgram, highSchoolEducation, associatesEducation, bachelorsEducation, mastersEducation, professionalEducation,
             doctorateEducation, otherEducation, otherEducationName, aerospaceEngineeringSpecialization, designSpecialization,
             electricalEngineeringSpecialization, industrialEngineeringSpecialization, manufacturingSpecialization, materialScienceSpecialization,
             mechanicalEngineeringSpecialization,  projectManagementSpecialization, roboticsSpecialization, softwareSpecialization, systemsEngineeringSpecialization, otherSpecialization,
             otherSpecializationName, systemsEngineeringExpertise, statementOfWorkExpertise))  
        conn.commit()

        # On success return success and join code
        return jsonify({"success": True, "joinCode": joinCode, "playerId": playerId})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})
    

# Joins a game creating a player for a given session IF that session exists
def join():
    try:
        # First pull data request, must have valid join code
        data = request.json
        name = data.get('name')
        color = data.get('color')
        participationReason = data.get('participationReason')
        gender = data.get('gender')
        age = data.get('age')
        country = data.get('country')
        hobbies = data.get('hobbies')
        isCollegeStudent = data.get('isCollegeStudent')
        university = data.get('university')
        degreeProgram = data.get('degreeProgram')
        yearsInProgram = data.get('yearsInProgram')
        highSchoolEducation = data.get('highSchoolEducation')
        associatesEducation = data.get('associatesEducation')
        bachelorsEducation = data.get('bachelorsEducation')
        mastersEducation = data.get('mastersEducation')
        professionalEducation = data.get('professionalEducation')
        doctorateEducation = data.get('doctorateEducation')
        otherEducation = data.get('otherEducation')
        otherEducationName = data.get('otherEducationName')
        aerospaceEngineeringSpecialization = data.get('aerospaceEngineeringSpecialization')
        designSpecialization = data.get('designSpecialization')
        electricalEngineeringSpecialization = data.get('electricalEngineeringSpecialization')
        industrialEngineeringSpecialization = data.get('industrialEngineeringSpecialization')
        manufacturingSpecialization = data.get('manufacturingSpecialization')
        materialScienceSpecialization = data.get('materialScienceSpecialization')
        mechanicalEngineeringSpecialization = data.get('mechanicalEngineeringSpecialization')
        projectManagementSpecialization = data.get('projectManagementSpecialization')
        roboticsSpecialization = data.get('roboticsSpecialization')
        softwareSpecialization = data.get('softwareSpecialization')
        systemsEngineeringSpecialization = data.get('systemsEngineeringSpecialization')
        otherSpecialization = data.get('otherSpecialization')
        otherSpecializationName = data.get('otherSpecializationName')
        systemsEngineeringExpertise = data.get('systemsEngineeringExpertise')
        statementOfWorkExpertise = data.get('statementOfWorkExpertise')
        joinCode = data.get('joinCode')

        # TODO return error if there are not required params

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

        # Now create new brief version of the player and insert them into the database
        cursor.execute(f"INSERT INTO PlayerBrief (Id, Name, Color, SessionId) VALUES (?, ?, ?, ?)", 
            (playerId, name, color, str(joinCode)))  
        conn.commit()

        # Now save extensive player information into the database
        cursor.execute(f'''INSERT INTO PlayerInformation (Id, Name, ParticipationReason, Gender, Age, Country, 
                       Hobbies, IsCollegeStudent, University, DegreeProgram, YearsInProgram, HighSchoolEducation, 
                       AssociatesEducation, BachelorsEducation, MastersEducation, ProfessionalEducation, 
                       DoctorateEducation, OtherEducation, OtherEducationName, AerospaceEngineeringSpecialization,
                       DesignSpecialization, ElectricalEngineeringSpecialization, IndustrialEngineeringSpecialization,
                       ManufacturingSpecialization, MaterialScienceSpecialization, MechanicalEngineeringSpecialization,
                       ProjectManagementSpecialization, RoboticsSpecialization, 
                       SoftwareSpecialization, SystemsEngineeringSpecialization, OtherSpecialization, OtherSpecializationName,
                       SystemsEngineeringExpertise, StatementOfWorkExpertise) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                       ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
            (playerId, name, participationReason, gender, age, country, hobbies, isCollegeStudent, university, degreeProgram,
             yearsInProgram, highSchoolEducation, associatesEducation, bachelorsEducation, mastersEducation, professionalEducation,
             doctorateEducation, otherEducation, otherEducationName, aerospaceEngineeringSpecialization, designSpecialization,
             electricalEngineeringSpecialization, industrialEngineeringSpecialization, manufacturingSpecialization, materialScienceSpecialization,
             mechanicalEngineeringSpecialization, projectManagementSpecialization, roboticsSpecialization, softwareSpecialization, systemsEngineeringSpecialization, otherSpecialization,
             otherSpecializationName, systemsEngineeringExpertise, statementOfWorkExpertise))  
        conn.commit()

        return jsonify({"success": True, "playerId": playerId})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})
    

# Removes a player from a session, called by the host to remove them or the player themselves to leave
# TODO must decide if it should delete the player data from the database (and all reliant round results) 
# or just change the session id to null. Will start with just changing session id so data remains in db
# for aggregate results.
def remove():
    try:
        # First check that required data is in request, must have valid playerId
        data = request.json
        playerId = data.get('playerId')

        # Create connection to Azure SQL Database
        conn = pyodbc.connect(AZURE_SQL_CONNECTION_STRING, timeout=120)
        cursor = conn.cursor()

        # Ensure player exists
        cursor.execute(f"SELECT * FROM PlayerBrief WHERE Id = ?", (str(playerId)))
        player = cursor.fetchone()
        if player is None:
            return jsonify({"error": "Player not found"})
        
        cursor.execute(f"UPDATE PlayerBrief SET SessionId = Null WHERE Id = ?", str(playerId))
        conn.commit()

        return jsonify({"success": True})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})


# Saves the result for one player for one round of the tournament. Includes shots, cost, and solvers played with
def roundResult():
    try:
        # Save player's results for a round in the tournament
        # First check that required data is in request, must have valid Id for Player,
        # as well as shot, cost, and round information
        data = request.json
        id = data.get('playerId')
        shots = data.get('shots')
        cost = data.get('cost')
        solverOne = data.get('solverOne')
        solverTwo = data.get('solverTwo')
        solverThree = data.get('solverThree')
        architecture = data.get('architecture')
        round = data.get('round')
        score = data.get('score')
        # if score is none save it as -1
        if score is None:
            score = -1

        # Create connection to Azure SQL Database
        conn = pyodbc.connect(AZURE_SQL_CONNECTION_STRING, timeout=120)
        cursor = conn.cursor()

        # Check that player exists
        cursor.execute(f"SELECT * FROM PlayerBrief WHERE Id = ?", (str(id)))
        player = cursor.fetchone()
        if player is None:
            return jsonify({"error": "Player not found"})
        
        # solver types: quantity is dependent on round number, there may be 1 (rounds 1 and 2), 
        # 2 (round 3), or 3 (round 4)
        # So space is reserved for 3 solvers for each round result but value may be None / Null

        # Now create new Round Result and insert into its table
        cursor.execute(f"INSERT INTO RoundResult (Round, Shots, Cost, SolverOne, SolverTwo, SolverThree, PlayerId, Architecture, Score) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                       (str(round), str(shots), str(cost), solverOne, solverTwo, solverThree, str(id), architecture, str(score)))  
        conn.commit()

        return jsonify({"success": True})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})
    
# Retreives ALL Round Results to show aggregate results across all tournaments played before. 
def allResults():
    try:
        # Create connection to Azure SQL Database
        conn = pyodbc.connect(AZURE_SQL_CONNECTION_STRING, timeout=120)
        cursor = conn.cursor()

        # Get all round results from Tournament Stages
        cursor.execute("SELECT * FROM RoundResult JOIN PlayerBrief ON RoundResult.PlayerId = PlayerBrief.Id WHERE Round > 5")
        results = cursor.fetchall()

        #  pyodbc.Row objects are not json serializable so convert and coerce any values not serializable (like decimals) into strings
        # results = [tuple(row) for row in results] # Saves as a tuple, harder to read on FE
        # json_string = json.dumps(results, default=str)
        resultList = []
        for result in results:
            resultList.append({"id": result.Id, "name": result.Name, "color": result.Color, "score": result.Score, "round": result.Round, "shots": result.Shots, "cost": result.Cost, "solverOne": result.SolverOne, "solverTwo": result.SolverTwo, "solverThree": result.SolverThree, "architecture": result.Architecture})

        # Now return all results
        return  jsonify({"results": resultList})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})
    
# Saves the result of a player playing free roam modules in the playground. includes shots, distance remaining to hole (up to 2 decimal places), solver used, and module selected, as well as the player's id 
def freeRoamResult():
    try:
        # Save player's results for a round in the tournament
        # First check that required data is in request, must have valid Id for Player,
        # as well as shot, cost, and round information
        data = request.json
        id = data.get('playerId')
        shots = data.get('shots')
        distance = data.get('distance')
        solver = data.get('solver')
        module = data.get('module')

        # Create connection to Azure SQL Database
        conn = pyodbc.connect(AZURE_SQL_CONNECTION_STRING, timeout=120)
        cursor = conn.cursor()

        # Check that player exists
        cursor.execute(f"SELECT * FROM PlayerBrief WHERE Id = ?", (str(id)))
        player = cursor.fetchone()
        if player is None:
            return jsonify({"error": "Player not found"})

        # Now create new Free Roam Result and insert into its table
        cursor.execute(f"INSERT INTO FreeRoamResult (Shots, Distance, Solver, Module, PlayerId) VALUES (?, ?, ?, ?, ?)", 
                       (str(shots), str(distance), solver, module, str(id)))  
        conn.commit()

        return jsonify({"success": True})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})
    
# Saves the result of a player Free roam survey 
# The number stored per module is for a solver as an int that can represent multiple solvers as follows:
# 1 -> Professional
# 2 -> Amateur
# 3 -> Specialist
# 4 -> Professional and Amateur
# 5 -> Professional and Specialist
# 6 -> Amateur and Specialist
# 7 -> Professional, Amateur, and Specialist (could be stored in 3 bits!)
def freeRoamSurvey():
    try:
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

        # Create connection to Azure SQL Database
        conn = pyodbc.connect(AZURE_SQL_CONNECTION_STRING, timeout=120)
        cursor = conn.cursor()

        # Check that player exists
        cursor.execute(f"SELECT * FROM PlayerBrief WHERE Id = ?", (str(id)))
        player = cursor.fetchone()
        if player is None:
            return jsonify({"error": "Player not found"})

        # Now create new Free Roam Result and insert into its table
        cursor.execute(f"INSERT INTO FreeRoamSurvey (Drive, Long, Fairway, Short, Putt, PlayerId) VALUES (?, ?, ?, ?, ?, ?)", 
                       (str(drive), str(long), str(fairway), str(short), str(putt), str(id)))  
        conn.commit()

        return jsonify({"success": True})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})
    