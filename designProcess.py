from flask import jsonify, request
from environmentSecrets import VT_MYSQL_HOST, VT_MYSQL_DB, VT_MYSQL_USER, VT_MYSQL_PASSWORD, VT_MYSQL_PORT
import pymysql
import pymysql.cursors

db = pymysql.connections.Connection(
    host=VT_MYSQL_HOST,
    user=VT_MYSQL_USER,
    password=VT_MYSQL_PASSWORD,
    database=VT_MYSQL_DB,
    port=VT_MYSQL_PORT
)

# write personal info to db (hash and salt pw)
def saveNewUser():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        gender = data.get('gender')
        age = data.get('age')
        ethnicity = data.get('ethnicity')
        employer = data.get('employer')
        team = data.get('team')
        title = data.get('title')
        bachelorsEducation = data.get('bachelorsEducation')
        mastersEducation = data.get('mastersEducation')
        doctorateEducation = data.get('doctorateEducation')
        otherEducation = data.get('otherEducation')
        otherEducationName = data.get('otherEducationName')
        aerodynamicsSpecialization = data.get('aerodynamicsSpecialization')
        computerScienceSpecialization = data.get('computerScienceSpecialization')
        electricalEngineeringSpecialization = data.get('electricalEngineeringSpecialization')
        electromagneticsSpecialization = data.get('electromagneticsSpecialization')
        environmentalTestingSpecialization = data.get('environmentalTestingSpecialization')
        logisticsSpecialization = data.get('logisticsSpecialization')
        manufacturingSpecialization = data.get('manufacturingSpecialization')
        mechanicalDesignSpecialization = data.get('mechanicalDesignSpecialization')
        operationsResearchSpecialization = data.get('operationsResearchSpecialization')
        projectManagementSpecialization = data.get('projectManagementSpecialization')
        systemsEngineeringSpecialization = data.get('systemsEngineeringSpecialization')
        structuralAnalysisSpecialization = data.get('structuralAnalysisSpecialization')
        threatAnalysisSpecialization = data.get('threatAnalysisSpecialization')
        otherSpecializationName = data.get('otherSpecializationName')
        otherSpecialization = data.get('otherSpecialization')
        shipyardAgency = data.get('shipyardAgency')
        navseaAgency = data.get('navseaAgency')
        nswcDahlgrenAgency = data.get('nswcDahlgrenAgency')
        nswcCarderockAgency = data.get('nswcCarderockAgency')
        opnavAgency = data.get('opnavAgency')
        pentagonAgency = data.get('pentagonAgency')
        otherNswcAgencyName = data.get('otherNswcAgencyName')
        otherAgency = data.get('otherAgency')
        riskAnalysisExperience = data.get('riskAnalysisExperience')
        supplierExperience = data.get('supplierExperience')
        projectContextFamiliarity = data.get('projectContextFamiliarity')
        navyPlatformFamiliarity = data.get('navyPlatformFamiliarity')
        designChangeCharacteristicsFamiliarity = data.get('designChangeCharacteristicsFamiliarity')

        cursor = db.cursor(pymysql.cursors.DictCursor)

        # Save information about session itself
        cursor.execute(f"SELECT * FROM Activity")

        activities = cursor.fetchall()
        print(activities)
        activitiesFound = []
        if activities is None:
            return jsonify({"error": "Session not found"})
        else: 
            for activity in activities:
                activitiesFound.append(activity)

        return jsonify({"success": True, "activities found:": activitiesFound})

    except Exception as e:
        print(e)
        return jsonify({"success": False, "exception": str(e)})
    
# write a set of records to db under one measurement period
def saveNewMeasurementPeriod():
    try:
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
        customPerformanceWeight = data.get('customPerformanceWeight')
        reasoning = data.get('reasoning')

        # if score is none save it as -1
        if score is None:
            score = -1

        # Create connection to VT MySQL Database
        cursor = db.cursor(pymysql.cursors.DictCursor)

        # Check that player exists
        cursor.execute(f"SELECT * FROM PlayerBrief WHERE Id = ?", (str(id)))
        player = cursor.fetchone()
        if player is None:
            return jsonify({"error": "Player not found"})
        
        # solver types: quantity is dependent on round number, there may be 1 (rounds 1 and 2), 
        # 2 (round 3), or 3 (round 4)
        # So space is reserved for 3 solvers for each round result but value may be None / Null

        # Now create new Round Result and insert into its table
        cursor.execute(f"INSERT INTO RoundResult (Round, Shots, Cost, SolverOne, SolverTwo, SolverThree, PlayerId, Architecture, Score, CustomPerformanceWeight, Reasoning) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
            (str(round), str(shots), str(cost), solverOne, solverTwo, solverThree, str(id), architecture, str(score), customPerformanceWeight, str(reasoning)))  
        conn.commit()




        return jsonify({"success": True, "activities found:": activitiesFound})

    except Exception as e:
        print(e)
        return jsonify({"success": False, "exception": str(e)})

# retreive all records from db

# check login matches 

# TODO reset pw