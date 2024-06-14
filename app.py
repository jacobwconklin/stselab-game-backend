import os
import pyodbc
from dotenv import load_dotenv
load_dotenv()

import requests

# Stse-lab Golf Project Functions:
from users import host, join, roundResult, remove, freeRoamResult, freeRoamSurvey, allResults, armRoundResult, diceResult
from session import sessionStatus, advanceSession, roundResults, finalResults, surveysSubmitted, playersInSession, endSession, armFinalResults, armRoundResults, jumpToArmMission

# Navy Design Process Project Functions:
from designProcess import saveNewUser, saveNewMeasurementPeriod, checkLogin, getAllActivityRecords, getAllMeasurementPeriods, getActivityRecordsForPeriod, getAllMeasurementPeriodsForUser, getAllUserRecords, getUserDetails, checkEmailExists, getMeasurementPeriodsInRange, leaveProject, checkDuplicateMeasurementPeriod

from flask import (Flask, redirect, render_template, request,
                   send_from_directory, url_for, jsonify, json)
from flask_cors import CORS
from flask_mail import Mail
from flask_mail import Message

app = Flask(__name__)
CORS(app)

from environmentSecrets import ADMIN_EMAIL_PASSWORD

# email credentials:
app.config.update(dict(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USE_SSL=False,
    MAIL_USERNAME = 'design.process.survey@gmail.com',
    MAIL_PASSWORD = ADMIN_EMAIL_PASSWORD
))

mail = Mail(app)

# Temporary global variables before database is connected
serverStorageCount = 0
users = [] # May still be usefulf for watching and printing data in compared to data in db, but not currently used.

@app.route('/')
def index():
    print('Request for index page received')
    return render_template('index.html')

@app.route('/testdb')

# Health check
@app.route('/health')
def health():
    try:
        # Could also verify database connection here (and any other dependencies)  
        # be careful as Azul uses this endpoint to check that the app is running, and may restart the deployed version if it fails to get 
        # a 200 response from this endpoint.
        return jsonify({'status': 'healthy'}), 200
    except Exception as e:
        print(e)
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/hello', methods=['POST'])
def hello():
   name = request.form.get('name')
   if name:
       print('Request for hello page received with name=%s' % name)
       return render_template('hello.html', name = name)
   else:
       print('Request for hello page received with no name or blank name -- redirecting')
       return redirect(url_for('index'))
   
# Used to send emails from Design Process Survey Admin to users. Kept in this app.py file because of the way
#  flask_mail interacts with flask. 
@app.route('/sendEmail', methods=['POST'])
def sendEmail():
    try:
        data = request.json
        email = data.get('email')
        message = data.get('message')
        print("Got message: " + message)
        # Send test email
        msg = Message(
            subject="Design Process Survey Admin Message",
            sender="design.process.survey@gmail.com",
            recipients=[email],
            html=f"""
                <b>{message}</b>
            """
                  )
        mail.send(msg)

        return jsonify({"success": True})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})
   
# All real methods to be used by application:

# REST API Endpoints:

# Routing for endpoints so this file isn't out of hand
   
# Session routes handled in session.py
app.add_url_rule('/session/status', 'session/status', sessionStatus, methods=['POST'])
app.add_url_rule('/session/players', 'session/players', playersInSession, methods=['POST'])
app.add_url_rule('/session/end', 'session/end', endSession, methods=['POST'])
app.add_url_rule('/session/advance', 'session/advance', advanceSession, methods=['POST'])
app.add_url_rule('/session/roundresults', 'session/roundresults', roundResults, methods=['POST'])
app.add_url_rule('/session/finalresults', 'session/finalresults', finalResults, methods=['POST'])
app.add_url_rule('/session/surveyssubmitted', 'session/surveyssubmitted', surveysSubmitted, methods=['POST'])

# Mechanical Arm Mission:
app.add_url_rule('/session/armroundresults', 'session/armroundresults', armRoundResults, methods=['POST'])
app.add_url_rule('/session/armfinalresults', 'session/armfinalresults', armFinalResults, methods=['POST'])
app.add_url_rule('/session/jumptoarmmission', 'session/jumptoarmmission', jumpToArmMission, methods=['POST'])

# User routes handled in users.py
app.add_url_rule('/player/host', 'player/host', host, methods=['POST'])
app.add_url_rule('/player/join', 'player/join', join, methods=['POST'])
app.add_url_rule('/player/roundResult', 'player/roundResult', roundResult, methods=['POST'])
app.add_url_rule('/player/remove', 'player/remove', remove, methods=['POST'])
app.add_url_rule('/player/freeRoamResult', 'player/freeRoamResult', freeRoamResult, methods=['POST'])
app.add_url_rule('/player/freeRoamSurvey', 'player/freeRoamSurvey', freeRoamSurvey, methods=['POST'])
app.add_url_rule('/player/diceResult', 'player/diceResult', diceResult, methods=['POST'])
app.add_url_rule('/player/allResults', 'player/allResults', allResults, methods=['GET'])
# Mechanical Arm Mission:
app.add_url_rule('/player/armRoundResult', 'player/armRoundResult', armRoundResult, methods=['POST'])



# For Navy Design Process Project:
app.add_url_rule('/navydp/saveNewUser', 'saveNewUser', saveNewUser, methods=['POST'])
app.add_url_rule('/navydp/saveNewMeasurementPeriod', 'saveNewMeasurementPeriod', saveNewMeasurementPeriod, methods=['POST'])
app.add_url_rule('/navydp/checkLogin', 'checkLogin', checkLogin, methods=['POST'])
app.add_url_rule('/navydp/getAllActivityRecords', 'getAllActivityRecords', getAllActivityRecords, methods=['GET'])
app.add_url_rule('/navydp/getActivityRecordsForPeriod', 'getActivityRecordsForPeriod', getActivityRecordsForPeriod, methods=['POST'])
app.add_url_rule('/navydp/getAllMeasurementPeriods', 'getAllMeasurementPeriods', getAllMeasurementPeriods, methods=['POST']) 
app.add_url_rule('/navydp/getAllMeasurementPeriodsForUser', 'getAllMeasurementPeriodsForUser', getAllMeasurementPeriodsForUser, methods=['POST'])
app.add_url_rule('/navydp/getAllUserRecords', 'getAllUserRecords', getAllUserRecords, methods=['POST'])
app.add_url_rule('/navydp/getUserDetails', 'getUserDetails', getUserDetails, methods=['POST'])
app.add_url_rule('/navydp/verifyEmail', 'verifyEmail', checkEmailExists, methods=['POST'])
app.add_url_rule('/navydp/getMeasurementPeriodsInRange', 'getMeasurementPeriodsInRange', getMeasurementPeriodsInRange, methods=['POST'])
app.add_url_rule('/navydp/leaveProject', 'leaveProject', leaveProject, methods=['POST'])
app.add_url_rule('/navydp/checkDuplicateMeasurementPeriod', 'checkDuplicateMeasurementPeriod', checkDuplicateMeasurementPeriod, methods=['POST'])




if __name__ == '__main__':
    app.run()