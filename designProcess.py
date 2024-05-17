from flask import jsonify, request
from environmentSecrets import VT_MYSQL_HOST, VT_MYSQL_DB, VT_MYSQL_USER, VT_MYSQL_PASSWORD, VT_MYSQL_PORT
import pymysql
import pymysql.cursors
import hashlib


# helper function to hash and salt passwords
def hashPassword(password):
    # TODO change and move salt to secrets, it does no good in a public github repo ... 
    salt = "STSE-SALT-Vamolaentao"
    combinedString = salt + password
    encoded = combinedString.encode()
    hashResult = hashlib.sha512( encoded ).hexdigest()
    return str(hashResult)

# Function to prevent SQL injection attacks
def sanitizeInput(input):
    return str(input).replace("'", "''").replace(";", "").replace("--", "- -")

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

        data = request.json
        activities = data.get('activities')
        email = sanitizeInput(data.get('email'))
        startDate = sanitizeInput(data.get('startDate'))
        endDate = sanitizeInput(data.get('endDate'))
        entered = sanitizeInput(data.get('entered'))
        totalDuration = sanitizeInput(data.get('totalDuration'))

        # Create connection to VT MySQL Database
        cursor = db.cursor(pymysql.cursors.DictCursor)

        # Check that user exists
        # cursor.execute(f"SELECT * FROM User WHERE email = '{(str(email))}'")
        # user = cursor.fetchone()
        # if user is None:
        #     return jsonify({"error": "User not found"})
        
        # Now create new Measurement Period and insert into its table
        sqlString = f"INSERT INTO MeasurementPeriod (Email, StartDate, EndDate, Entered, TotalDuration) VALUES ('{email}', '{startDate}', '{endDate}', '{entered}', '{totalDuration}')"
        cursor.execute(sqlString)
        db.commit()
            
        # need to get id of measurement period to insert into activity record
        sqlString = "SELECT LAST_INSERT_ID()"
        cursor.execute(sqlString)
        newMeasurementPeriod = cursor.fetchone()
        db.commit()

        numberOfActivities = 0
        for rawActivity in activities:
            activity = sanitizeJson(rawActivity)
            q1 = activity.get('question1', None)
            q2 = activity.get('question2', None)
            q3 = activity.get('question3', None)
            q4 = activity.get('question4', None)
            sqlString = f"INSERT INTO ActivityRecord (MeasurementPeriod, Type, Duration, Question1, Question2, Question3, Question4) VALUES ('{newMeasurementPeriod['LAST_INSERT_ID()']}', '{activity['type']}', '{activity['duration']}', '{q1}', '{q2}', '{q3}', '{q4}')"
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




# retreive all user records from db
def getAllUserRecords():
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
        # TODO may want to apply a join / filter to only get users with at least one measurement period
        cursor.execute(f"SELECT Email FROM User")
        users = cursor.fetchall()
        # For each user, pull all measurement periods and calculate latest, total hours, and total number of periods
        finalUsers = []
        for user in users:
            cursor.execute(f"SELECT * FROM MeasurementPeriod WHERE Email = '{user['Email']}'")
            periods = cursor.fetchall()
            user['numberOfPeriods'] = len(periods)
            totalHoursForUser = 0
            user['lastRecordedPeriodEndDate'] = None
            user['lastRecordedPeriodStartDate'] = None
            for period in periods:
                # No need to iterate through every activity here thanks to totalDuration cursor.execute(f"SELECT * FROM ActivityRecord WHERE MeasurementPeriod = '{period['Id']}'")
                # activities = cursor.fetchall()
                # for activity in activities:
                #     user['totalHours'] += activity['Duration']
                if user['lastRecordedPeriodEndDate'] is None or period['EndDate'] > user['lastRecordedPeriodEndDate']:
                    user['lastRecordedPeriodEndDate'] = period['EndDate']
                    user['lastRecordedPeriodStartDate'] = period['StartDate']
                if period['TotalDuration']:
                    totalHoursForUser += period['TotalDuration']
            user['totalHoursRecorded'] = totalHoursForUser
            finalUsers.append(user)

        return jsonify({"success": True, "data": finalUsers})
    except Exception as e:
        print(e)
        return jsonify({"success": False, "exception": str(e)})    
    finally:
        if (cursor != None):
            cursor.close()
        if (db != None):
            db.close()
    
# retreive detiled user information from db
def getUserDetails():
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
        cursor.execute(f"SELECT * FROM User WHERE Email = '{(sanitizeInput(request.json.get('email')))}'")
        records = cursor.fetchone()
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
    
# retreive all activity records for a specified measurement period from db
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
        print("here")
        print(request.json.get('measurementPeriod'))
        print(sanitizeInput(str(request.json.get('measurementPeriod'))))
        cursor.execute(f"SELECT * FROM ActivityRecord WHERE MeasurementPeriod = '{(sanitizeInput(str(request.json.get('measurementPeriod'))))}'")
        print("executed sql")
        records = cursor.fetchall()
        print(records)
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

# retreive all measurement periods for a specified user from db
def getAllMeasurementPeriodsForUser():
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
        cursor.execute(f"SELECT * FROM MeasurementPeriod WHERE Email = '{(sanitizeInput(request.json.get('email')))}'")
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