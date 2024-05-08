from flask import jsonify, request
from environmentSecrets import VT_MYSQL_HOST, VT_MYSQL_DB, VT_MYSQL_USER, VT_MYSQL_PASSWORD, VT_MYSQL_PORT
import pymysql
import pymysql.cursors
import hashlib


# helper function to hash and salt passwords
def hashPassword(password):
    salt = "STSE-SALT-Vamolaentao"
    combinedString = salt + password
    encoded = combinedString.encode()
    hashResult = hashlib.sha512( encoded ).hexdigest()
    return str(hashResult)

# Function to prevent SQL injection attacks
def sanitizeInput(input):
    return input.replace("'", "''").replace(";", "").replace("--", "- -")

# Sanitize the entire incoming JSON
def sanitizeJson(json):
    for key in json:
        json[key] = sanitizeInput(json[key])
    return json


# write personal info to db (hash and salt pw)
def saveNewUser():
    try:

        db = None
        cursor = None

        db = pymysql.connections.Connection(
            host=VT_MYSQL_HOST,
            user=VT_MYSQL_USER,
            password=VT_MYSQL_PASSWORD,
            database=VT_MYSQL_DB,
            port=VT_MYSQL_PORT
        )

        progress = "Start of function"
        
        data = sanitizeJson(request.json)
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

        
        progress = "got params"
        
        # Create connection to VT MySQL Database
        cursor = db.cursor(pymysql.cursors.DictCursor)

        progress = "got cursor"

        sqlString = f"INSERT INTO User (Email, Password, Gender, Age, Ethnicity, Employer, Team, Title, BachelorsEducation, MastersEducation, DoctorateEducation, OtherEducation, OtherEducationName, AerodynamicsSpecialization, ComputerScienceSpecialization, ElectricalEngineeringSpecialization, ElectromagneticsSpecialization, EnvironmentalTestingSpecialization, LogisticsSpecialization, ManufacturingSpecialization, MechanicalDesignSpecialization, OperationsResearchSpecialization, ProjectManagementSpecialization, SystemsEngineeringSpecialization, StructuralAnalysisSpecialization, ThreatAnalysisSpecialization, OtherSpecializationName, OtherSpecialization, ShipyardAgency, NavseaAgency, NswcDahlgrenAgency, NswcCarderockAgency, OpnavAgency, PentagonAgency, OtherNswcAgencyName, OtherAgency, RiskAnalysisExperience, SupplierExperience, ProjectContextFamiliarity, NavyPlatformFamiliarity, DesignChangeCharacteristicsFamiliarity ) VALUES ('{email}', '{hashPassword(password)}', '{gender}', '{age}', '{ethnicity}', '{employer}', '{team}', '{title}', '{bachelorsEducation}', '{mastersEducation}', '{doctorateEducation}', '{otherEducation}', '{otherEducationName}', '{aerodynamicsSpecialization}', '{computerScienceSpecialization}', '{electricalEngineeringSpecialization}', '{electromagneticsSpecialization}', '{environmentalTestingSpecialization}', '{logisticsSpecialization}', '{manufacturingSpecialization}', '{mechanicalDesignSpecialization}', '{operationsResearchSpecialization}', '{projectManagementSpecialization}', '{systemsEngineeringSpecialization}', '{structuralAnalysisSpecialization}', '{threatAnalysisSpecialization}', '{otherSpecializationName}', '{otherSpecialization}', '{shipyardAgency}', '{navseaAgency}', '{nswcDahlgrenAgency}', '{nswcCarderockAgency}', '{opnavAgency}', '{pentagonAgency}', '{otherNswcAgencyName}', '{otherAgency}', '{riskAnalysisExperience}', '{supplierExperience}', '{projectContextFamiliarity}', '{navyPlatformFamiliarity}', '{designChangeCharacteristicsFamiliarity}')"

        
        progress = "made sqlstring: " + sqlString

        cursor.execute(sqlString)

        progress = "executed sqlstring"

        db.commit()

        progress = "committed"

        return jsonify({"success": True})

    except Exception as e:
        print(e)
        return jsonify({"success": False, "exception": str(e), "progress": progress})
    
    finally:
        if (cursor != None):
            cursor.close()
        if (db != None):
            db.close()

# write a set of records to db under one measurement period
def saveNewMeasurementPeriod():
    try:

        db = None
        cursor = None

        db = pymysql.connections.Connection(
            host=VT_MYSQL_HOST,
            user=VT_MYSQL_USER,
            password=VT_MYSQL_PASSWORD,
            database=VT_MYSQL_DB,
            port=VT_MYSQL_PORT
        )

        data = sanitizeJson(request.json)
        activities = data.get('activities')
        email = data.get('email')
        startDate = data.get('startDate')
        endDate = data.get('endDate')
        entered = data.get('entered')

        # Create connection to VT MySQL Database
        cursor = db.cursor(pymysql.cursors.DictCursor)

        # Check that user exists
        # cursor.execute(f"SELECT * FROM User WHERE email = ?", (str(email)))
        # user = cursor.fetchone()
        # if user is None:
        #     return jsonify({"error": "User not found"})
        
        # Now create new Measurement Period and insert into its table
        sqlString = f"INSERT INTO MeasurementPeriod (Email, StartDate, EndDate, Entered) VALUES ('{email}', '{startDate}', '{endDate}', '{entered}')"
        cursor.execute(sqlString)
        db.commit()
            
        # need to get id of measurement period to insert into activity record
        sqlString = "SELECT LAST_INSERT_ID()"
        cursor.execute(sqlString)
        newMeasurementPeriod = cursor.fetchone()
        db.commit()

        numberOfActivities = 0
        for activity in activities:
            sqlString = f"INSERT INTO ActivityRecord (MeasurementPeriod, Type, Duration, Question1, Question2, Question3, pointScale) VALUES ('{newMeasurementPeriod['LAST_INSERT_ID()']}', '{activity['type']}', '{activity['duration']}', '{activity['question1']}', '{activity['question2']}', '{activity['question3']}', {activity['pointScale']})"
            cursor.execute(sqlString)
            db.commit()
            numberOfActivities += 1

        return jsonify({"success": True, "number-of-activities": numberOfActivities})

    except Exception as e:
        print(e)
        return jsonify({"success": False, "exception": str(e)})
    finally:
        if (cursor != None):
            cursor.close()
        if (db != None):
            db.close()

# retreive all activity records from db
def getAllActivityRecords():
    try:
        db = None
        cursor = None

        db = pymysql.connections.Connection(
            host=VT_MYSQL_HOST,
            user=VT_MYSQL_USER,
            password=VT_MYSQL_PASSWORD,
            database=VT_MYSQL_DB,
            port=VT_MYSQL_PORT
        )

        cursor = db.cursor(pymysql.cursors.DictCursor)
        cursor.execute(f"SELECT * FROM ActivityRecord")
        records = cursor.fetchall()
        return jsonify({"success": True, "data": records})
    except Exception as e:
        print(e)
        return jsonify({"success": False, "exception": str(e)})    
    finally:
        if (cursor != None):
            cursor.close()
        if (db != None):
            db.close()
    
# retreive all activity records from db
def getActivityRecordsForPeriod():
    try:
        db = None
        cursor = None

        db = pymysql.connections.Connection(
            host=VT_MYSQL_HOST,
            user=VT_MYSQL_USER,
            password=VT_MYSQL_PASSWORD,
            database=VT_MYSQL_DB,
            port=VT_MYSQL_PORT
        )

        cursor = db.cursor(pymysql.cursors.DictCursor)
        cursor.execute(f"SELECT * FROM ActivityRecord WHERE MeasurementPeriod = ?", (sanitizeInput(request.json.get('measurementPeriod'))))
        records = cursor.fetchall()
        return jsonify({"success": True, "data": records})
    except Exception as e:
        print(e)
        return jsonify({"success": False, "exception": str(e)})    
    finally:
        if (cursor != None):
            cursor.close()
        if (db != None):
            db.close()
    
# retreive all measurement periods from db
def getAllMeasurementPeriods():
    try:
        db = None
        cursor = None

        db = pymysql.connections.Connection(
            host=VT_MYSQL_HOST,
            user=VT_MYSQL_USER,
            password=VT_MYSQL_PASSWORD,
            database=VT_MYSQL_DB,
            port=VT_MYSQL_PORT
        )

        cursor = db.cursor(pymysql.cursors.DictCursor)
        cursor.execute(f"SELECT * FROM MeasurementPeriod")
        records = cursor.fetchall()
        return jsonify({"success": True, "data": records})
    except Exception as e:
        print(e)
        return jsonify({"success": False, "exception": str(e)})    
    finally:
        if (cursor != None):
            cursor.close()
        if (db != None):
            db.close()

# check login matches 
def checkLogin():
    try:
        db = None
        cursor = None

        db = pymysql.connections.Connection(
            host=VT_MYSQL_HOST,
            user=VT_MYSQL_USER,
            password=VT_MYSQL_PASSWORD,
            database=VT_MYSQL_DB,
            port=VT_MYSQL_PORT
        )
        
        data = sanitizeJson(request.json)

        email = data.get('email')
        password = data.get('password')

        cursor = db.cursor(pymysql.cursors.DictCursor)
        sqlString = f"SELECT * FROM User WHERE Email = '{email}' AND Password = '{hashPassword(password)}'"
        cursor.execute(sqlString)
        user = cursor.fetchone()
        if user is None:
            return jsonify({"success": False, "error": "User not found"})
        return jsonify({"success": True}) # TODO figure out if creating / adding a token here? 
    except Exception as e:
        print(e)
        return jsonify({"success": False, "exception": str(e)})    
    finally:
        if (cursor != None):
            cursor.close()
        if (db != None):
            db.close()

# TODO reset pw