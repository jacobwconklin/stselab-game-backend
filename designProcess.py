from flask import jsonify, request
from environmentSecrets import VT_MYSQL_HOST, VT_MYSQL_DESIGN_PROCESS_DB, VT_MYSQL_USER, VT_MYSQL_PASSWORD, VT_MYSQL_PORT, VT_MYSQL_PASSWORD_SALT
import pymysql
import pymysql.cursors
import hashlib


# helper function to hash and salt passwords
def hashPassword(password):
    # TODO change and move salt to secrets, it does no good in a public github repo ... 
    salt = VT_MYSQL_PASSWORD_SALT
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
        db = pymysql.connections.Connection(host=VT_MYSQL_HOST, user=VT_MYSQL_USER, password=VT_MYSQL_PASSWORD, database=VT_MYSQL_DESIGN_PROCESS_DB, port=VT_MYSQL_PORT)

        progress = "Start of function"

        print(progress)
        
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
        joinedProjectDate = data.get('joinedProjectDate')

        
        progress = "got params"
        print(progress)
        
        # Create connection to VT MySQL Database
        cursor = db.cursor(pymysql.cursors.DictCursor)

        progress = "got cursor"
        print(progress)

        sqlString = f"INSERT INTO User (Email, Gender, Age, Ethnicity, Employer, Team, Title, BachelorsEducation, MastersEducation, DoctorateEducation, OtherEducation, OtherEducationName, AerodynamicsSpecialization, ComputerScienceSpecialization, ElectricalEngineeringSpecialization, ElectromagneticsSpecialization, EnvironmentalTestingSpecialization, LogisticsSpecialization, ManufacturingSpecialization, MechanicalDesignSpecialization, OperationsResearchSpecialization, ProjectManagementSpecialization, SystemsEngineeringSpecialization, StructuralAnalysisSpecialization, ThreatAnalysisSpecialization, OtherSpecializationName, OtherSpecialization, ShipyardAgency, NavseaAgency, NswcDahlgrenAgency, NswcCarderockAgency, OpnavAgency, PentagonAgency, OtherNswcAgencyName, OtherAgency, RiskAnalysisExperience, SupplierExperience, ProjectContextFamiliarity, NavyPlatformFamiliarity, DesignChangeCharacteristicsFamiliarity, JoinedProjectDate ) VALUES ('{email}', '{gender}', '{age}', '{ethnicity}', '{employer}', '{team}', '{title}', '{bachelorsEducation}', '{mastersEducation}', '{doctorateEducation}', '{otherEducation}', '{otherEducationName}', '{aerodynamicsSpecialization}', '{computerScienceSpecialization}', '{electricalEngineeringSpecialization}', '{electromagneticsSpecialization}', '{environmentalTestingSpecialization}', '{logisticsSpecialization}', '{manufacturingSpecialization}', '{mechanicalDesignSpecialization}', '{operationsResearchSpecialization}', '{projectManagementSpecialization}', '{systemsEngineeringSpecialization}', '{structuralAnalysisSpecialization}', '{threatAnalysisSpecialization}', '{otherSpecializationName}', '{otherSpecialization}', '{shipyardAgency}', '{navseaAgency}', '{nswcDahlgrenAgency}', '{nswcCarderockAgency}', '{opnavAgency}', '{pentagonAgency}', '{otherNswcAgencyName}', '{otherAgency}', '{riskAnalysisExperience}', '{supplierExperience}', '{projectContextFamiliarity}', '{navyPlatformFamiliarity}', '{designChangeCharacteristicsFamiliarity}', '{joinedProjectDate}')"

        
        progress = "made sqlstring: " + sqlString
        print(progress)

        cursor.execute(sqlString)

        progress = "executed sqlstring"
        print(progress)

        db.commit()

        progress = "committed"
        print(progress)

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
            database=VT_MYSQL_DESIGN_PROCESS_DB,
            port=VT_MYSQL_PORT
        )

        data = request.json
        activities = data.get('activities')
        email = sanitizeInput(data.get('email'))
        startDate = sanitizeInput(data.get('startDate'))
        endDate = sanitizeInput(data.get('endDate'))
        entered = sanitizeInput(data.get('entered'))
        totalDuration = sanitizeInput(data.get('totalDuration'))
        duplicateDateDecision = data.get('duplicateDateDecision')

        # Create connection to VT MySQL Database
        cursor = db.cursor(pymysql.cursors.DictCursor)

        # Check that user exists
        sqlString = f"SELECT * FROM User WHERE Email = '{email}'"
        cursor.execute(sqlString)
        user = cursor.fetchone()
        if user is None:
            return jsonify({"error": "User not found"})
        
        # IF record is a duplicate, then duplicate date decision will be '1' to add the activities to the existing record, or '2' to overwrite the existing record. A '0' indicates it is not a duplicate.
        if duplicateDateDecision == 1:
            # Get the existing measurement period
            # need to get id of measurement period to insert into activity record
            sqlString = f"SELECT * FROM MeasurementPeriod WHERE Email = '{email}' AND StartDate = '{startDate}' AND EndDate = '{endDate}'"
            cursor.execute(sqlString)
            existingMeasurementPeriod = cursor.fetchone()
            if existingMeasurementPeriod is None:
                return jsonify({"error": "No existing measurement period found for this date range"})
            
            # Update measurement period with the sum of the new total duration and the existing total duration
            newTotalDuration = int(existingMeasurementPeriod['TotalDuration']) + int(totalDuration)
            sqlString = f"UPDATE MeasurementPeriod SET TotalDuration = '{newTotalDuration}' WHERE Id = '{existingMeasurementPeriod['Id']}'"
            cursor.execute(sqlString)
            db.commit()
            
            # Now save all of the new activities to the same old measurement period
            numberOfActivities = 0
            for rawActivity in activities:
                activity = sanitizeJson(rawActivity)
                q1 = activity.get('question1', None)
                q2 = activity.get('question2', None)
                q3 = activity.get('question3', None)
                q4 = activity.get('question4', None)
                sqlString = f"INSERT INTO ActivityRecord (MeasurementPeriod, Type, Duration, Question1, Question2, Question3, Question4) VALUES ('{existingMeasurementPeriod['Id']}', '{activity['type']}', '{activity['duration']}', '{q1}', '{q2}', '{q3}', '{q4}')"
                cursor.execute(sqlString)
                db.commit()
                numberOfActivities += 1

            return jsonify({"success": True, "number-of-activities": numberOfActivities})

        elif duplicateDateDecision == 2:
            # Delete the existing measurement period and all associated activity records, then add the new ones. Will have to delete
            # activities first as cascading delete is not set up
            sqlString = f"SELECT Id FROM MeasurementPeriod WHERE Email = '{email}' AND StartDate = '{startDate}' AND EndDate = '{endDate}'"
            cursor.execute(sqlString)
            existingMeasurementPeriod = cursor.fetchone()
            if existingMeasurementPeriod is None:
                return jsonify({"error": "No existing measurement period found for this date range"})
            existingMeasurementPeriodId = existingMeasurementPeriod['Id']
            sqlString = f"DELETE FROM ActivityRecord WHERE MeasurementPeriod = '{existingMeasurementPeriodId}'"
            cursor.execute(sqlString)
            db.commit()
            sqlString = f"DELETE FROM MeasurementPeriod WHERE Id = '{existingMeasurementPeriodId}'"
            cursor.execute(sqlString)

            # Now save all of the new info
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

        else:
            # Just save the new info
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

# check that email already exists, if not give pop-up that sends user to sign up page. 
def checkEmailExists():
    try:
        db = None
        cursor = None

        db = pymysql.connections.Connection(
            host=VT_MYSQL_HOST,
            user=VT_MYSQL_USER,
            password=VT_MYSQL_PASSWORD,
            database=VT_MYSQL_DESIGN_PROCESS_DB,
            port=VT_MYSQL_PORT
        )
        
        data = sanitizeJson(request.json)

        email = data.get('email')

        cursor = db.cursor(pymysql.cursors.DictCursor)
        sqlString = f"SELECT * FROM User WHERE Email = '{email}'"
        cursor.execute(sqlString)
        user = cursor.fetchone()
        if user is None:
            return jsonify({"success": False, "error": "User not found"})
        return jsonify({"success": True})
    except Exception as e:
        print(e)
        return jsonify({"success": False, "exception": str(e)})    
    finally:
        if (cursor != None):
            cursor.close()
        if (db != None):
            db.close()

# ADMIN FUNCTIONS

# Verify admin credentials
def checkAdminCredentials(email, password = None, token = None):
    try:
        db = None
        cursor = None

        db = pymysql.connections.Connection(
            host=VT_MYSQL_HOST,
            user=VT_MYSQL_USER,
            password=VT_MYSQL_PASSWORD,
            database=VT_MYSQL_DESIGN_PROCESS_DB,
            port=VT_MYSQL_PORT
        )

        # TODO could create a list of admin usernames / emails, but for now it will be hardcoded to just 'admin'
        if email != 'admin':
            return False
        
        hashedPassword = None
        if token:
            hashedPassword = token
        elif password:
            hashedPassword = hashPassword(password)
        else:
            return False

        cursor = db.cursor(pymysql.cursors.DictCursor)
        sqlString = f"SELECT * FROM User WHERE Email = '{email}' AND Password = '{hashedPassword}'"
        cursor.execute(sqlString)
        user = cursor.fetchone()
        if user is None:
            return False
        return hashedPassword  
    except Exception as e:
        print(e)
        return False
    finally:
        if (cursor != None):
            cursor.close()
        if (db != None):
            db.close()
            
# check admin login matches 
def checkLogin():
    try:
        data = sanitizeJson(request.json)
        email = data.get('email')
        password = data.get('password')
        adminHashPassword = checkAdminCredentials(email, password=password)
        if not adminHashPassword:
            return jsonify({"success": False, "error": "Invalid Admin Credentials"})
        else: 
            return jsonify({"success": True, "token": adminHashPassword})
    except Exception as e:
        print(e)
        return jsonify({"success": False, "exception": str(e)})    
    
# retreive detiled user information from db
def getUserDetails():
    try:
        db = None
        cursor = None

        data = sanitizeJson(request.json)
        if not checkAdminCredentials(email=data.get('adminEmail'), token=data.get('token')):
            return jsonify({"success": False, "error": "Invalid Admin Credentials"})
        
        db = pymysql.connections.Connection(host=VT_MYSQL_HOST, user=VT_MYSQL_USER, password=VT_MYSQL_PASSWORD, database=VT_MYSQL_DESIGN_PROCESS_DB, port=VT_MYSQL_PORT)
        cursor = db.cursor(pymysql.cursors.DictCursor)

        cursor.execute(f"SELECT * FROM User WHERE Email = '{data.get('email')}'")
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

        data = sanitizeJson(request.json)
        if not checkAdminCredentials(email=data.get('adminEmail'), token=data.get('token')):
            return jsonify({"success": False, "error": "Invalid Admin Credentials"})

        db = pymysql.connections.Connection(host=VT_MYSQL_HOST, user=VT_MYSQL_USER, password=VT_MYSQL_PASSWORD, database=VT_MYSQL_DESIGN_PROCESS_DB, port=VT_MYSQL_PORT)
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

        data = sanitizeJson(request.json)
        if not checkAdminCredentials(email=data.get('adminEmail'), token=data.get('token')):
            return jsonify({"success": False, "error": "Invalid Admin Credentials"})

        db = pymysql.connections.Connection(host=VT_MYSQL_HOST, user=VT_MYSQL_USER, password=VT_MYSQL_PASSWORD, database=VT_MYSQL_DESIGN_PROCESS_DB, port=VT_MYSQL_PORT)
        cursor = db.cursor(pymysql.cursors.DictCursor)

        cursor.execute(f"SELECT * FROM ActivityRecord WHERE MeasurementPeriod = '{data.get('measurementPeriod')}'")
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

        data = sanitizeJson(request.json)
        if not checkAdminCredentials(email=data.get('adminEmail'), token=data.get('token')):
            return jsonify({"success": False, "error": "Invalid Admin Credentials"})

        db = pymysql.connections.Connection(host=VT_MYSQL_HOST, user=VT_MYSQL_USER, password=VT_MYSQL_PASSWORD, database=VT_MYSQL_DESIGN_PROCESS_DB, port=VT_MYSQL_PORT)
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

        data = sanitizeJson(request.json)
        if not checkAdminCredentials(email=data.get('adminEmail'), token=data.get('token')):
            return jsonify({"success": False, "error": "Invalid Admin Credentials"})
        
        db = pymysql.connections.Connection(host=VT_MYSQL_HOST, user=VT_MYSQL_USER, password=VT_MYSQL_PASSWORD, database=VT_MYSQL_DESIGN_PROCESS_DB, port=VT_MYSQL_PORT)
        cursor = db.cursor(pymysql.cursors.DictCursor)

        cursor.execute(f"SELECT * FROM MeasurementPeriod WHERE Email = '{data.get('email')}'")
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

# retreive all user records from db
def getAllUserRecords():
    try:
        db = None
        cursor = None

        data = sanitizeJson(request.json)
        if not checkAdminCredentials(email=data.get('adminEmail'), token=data.get('token')):
            return jsonify({"success": False, "error": "Invalid Admin Credentials"})

        db = pymysql.connections.Connection(host=VT_MYSQL_HOST, user=VT_MYSQL_USER, password=VT_MYSQL_PASSWORD, database=VT_MYSQL_DESIGN_PROCESS_DB, port=VT_MYSQL_PORT)
        cursor = db.cursor(pymysql.cursors.DictCursor)

        # TODO may want to apply a join / filter to only get users with at least one measurement period
        cursor.execute(f"SELECT Email, JoinedProjectDate, LeftProjectDate FROM User")
        users = cursor.fetchall()
        # For each user, pull all measurement periods and calculate latest, total hours, and total number of periods
        finalUsers = []
        for user in users:
            # add email, joined project date, and left project date to finalUsers in lowercase
            newUser = {'email': user['Email'], 'joinedProjectDate': user['JoinedProjectDate'], 'leftProjectDate': user['LeftProjectDate']}
            cursor.execute(f"SELECT * FROM MeasurementPeriod WHERE Email = '{user['Email']}'")
            periods = cursor.fetchall()
            newUser['numberOfPeriods'] = len(periods)
            totalHoursForUser = 0
            newUser['lastRecordedPeriodEndDate'] = None
            newUser['lastRecordedPeriodStartDate'] = None
            for period in periods:
                # No need to iterate through every activity here thanks to totalDuration cursor.execute(f"SELECT * FROM ActivityRecord WHERE MeasurementPeriod = '{period['Id']}'")
                # activities = cursor.fetchall()
                # for activity in activities:
                #     user['totalHours'] += activity['Duration']
                if newUser['lastRecordedPeriodEndDate'] is None or period['EndDate'] > newUser['lastRecordedPeriodEndDate']:
                    newUser['lastRecordedPeriodEndDate'] = period['EndDate']
                    newUser['lastRecordedPeriodStartDate'] = period['StartDate']
                if period['TotalDuration']:
                    totalHoursForUser += period['TotalDuration']
            newUser['totalHoursRecorded'] = totalHoursForUser
            finalUsers.append(newUser)

        return jsonify({"success": True, "data": finalUsers})
    except Exception as e:
        print(e)
        return jsonify({"success": False, "exception": str(e)})    
    finally:
        if (cursor != None):
            cursor.close()
        if (db != None):
            db.close()

# Used for time view on the admin dashboard. Gives all measurement periods in a specific date range based on start date,
# and only shows records with totalDuration filled in ( > 0). Front end will group the values by email to display in a table view.
def getMeasurementPeriodsInRange():
    try:
        db = None
        cursor = None

        data = sanitizeJson(request.json)
        if not checkAdminCredentials(email=data.get('adminEmail'), token=data.get('token')):
            return jsonify({"success": False, "error": "Invalid Admin Credentials"})
        
        db = pymysql.connections.Connection(host=VT_MYSQL_HOST, user=VT_MYSQL_USER, password=VT_MYSQL_PASSWORD, database=VT_MYSQL_DESIGN_PROCESS_DB, port=VT_MYSQL_PORT)
        cursor = db.cursor(pymysql.cursors.DictCursor)

        earliestStartDate = data.get('earliestStartDate')
        latestStartDate = data.get('latestStartDate')

        cursor.execute(f"SELECT * FROM MeasurementPeriod WHERE TotalDuration > 0 AND StartDate >= '{earliestStartDate}' AND StartDate <= '{latestStartDate}'")

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

<<<<<<< HEAD
def exitSurvey ():
    data = request.json
    name = data.get("name")
    print(name)
    return jsonify({"success": True})
=======
# check if user already has a measurement period for the current date range
def checkDuplicateMeasurementPeriod():
    try:
        db = None
        cursor = None

        data = sanitizeJson(request.json)

        db = pymysql.connections.Connection(host=VT_MYSQL_HOST, user=VT_MYSQL_USER, password=VT_MYSQL_PASSWORD, database=VT_MYSQL_DESIGN_PROCESS_DB, port=VT_MYSQL_PORT)
        cursor = db.cursor(pymysql.cursors.DictCursor)

        email = data.get('email')
        startDate = data.get('startDate')
        endDate = data.get('endDate')

        cursor.execute(f"SELECT * FROM MeasurementPeriod WHERE Email = '{email}' AND StartDate = '{startDate}' AND EndDate = '{endDate}'")
        existingRecord = cursor.fetchone()

        isDuplicate = False
        if existingRecord:
            isDuplicate = True

        return jsonify({"success": True, "isDuplicate": isDuplicate})
    except Exception as e:
        print(e)
        return jsonify({"success": False, "exception": str(e)})    
    finally:
        if (cursor != None):
            cursor.close()
        if (db != None):
            db.close()

# Save to database the date that a user is leaving the project
def leaveProject():
    try:
        db = None
        cursor = None

        data = sanitizeJson(request.json)

        db = pymysql.connections.Connection(host=VT_MYSQL_HOST, user=VT_MYSQL_USER, password=VT_MYSQL_PASSWORD, database=VT_MYSQL_DESIGN_PROCESS_DB, port=VT_MYSQL_PORT)
        cursor = db.cursor(pymysql.cursors.DictCursor)

        email = data.get('email')
        leaveProjectDate = data.get('leaveProjectDate')

        cursor.execute(f"UPDATE User SET LeftProjectDate = '{leaveProjectDate}' WHERE Email = '{email}'")
        db.commit()

        return jsonify({"success": True})
    except Exception as e:
        print(e)
        return jsonify({"success": False, "exception": str(e)})    
    finally:
        if (cursor != None):
            cursor.close()
        if (db != None):
            db.close()


>>>>>>> 648ca5ca0c00d041e7322a4c15c0e3fe60d19379

'''
Using pymysql cursor:
cursor = db.cursor(pymysql.cursors.DictCursor)
sqlString = f"SELECT * FROM User WHERE Email = '{variable}' AND Password = '{variable2}'"
cursor.execute(sqlString)
oneValue = cursor.fetchone()
allValues = cursor.fetchall()
db.commit() # This will persist changes if inputing / manipulating db and not just grabbing a value
'''