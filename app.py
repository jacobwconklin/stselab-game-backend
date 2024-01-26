import os
import pyodbc as odbc
from dotenv import load_dotenv
load_dotenv()

from flask import (Flask, redirect, render_template, request,
                   send_from_directory, url_for, jsonify, json)
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Temporary global variables before database is connected
serverStorageCount = 0
users = []

@app.route('/')
def index():
   print('Request for index page received')
   return render_template('index.html')

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
   

# My methods:
@app.route('/addcount')
def addCount():
    global serverStorageCount
    serverStorageCount += 1
    return jsonify({"count": serverStorageCount})


# STSELab Demo Methods:
@app.route('/submitform', methods=['POST'])
def submitform():
    try:
        data = request.json
        firstName = data.get('firstName')
        lastName = data.get('lastName')
        num = data.get('num')
        birthDate = data.get('birthDate')
        pet = data.get('pet')
        color = data.get('color')
        global users
        newUser = {"id": len(users) + 1, "firstName": firstName, "lastName": lastName, "num": num, "birthDate": birthDate, "pet": pet, "color": color}
        users.append(newUser)
        return jsonify({"success": True, "user": newUser})
    except Exception as e:
        print(e)
        return jsonify({"error": e})
    
@app.route('/allusers')
def allusers():
    global users
    return jsonify({"users": users})

@app.route('/resetusers')
def resetusers():
    global users
    users = []
    return jsonify({"success": True})

@app.route('/testdb')
def testdb():
    connection_string = os.getenv('AZURE_SQL_CONNECTIONSTRING')
    conn = odbc.connect(connection_string)
    cursor = conn.cursor()
    # cursor.execute(f"INSERT INTO Persons (FirstName, LastName) VALUES (?, ?)", "lim", "Kob")
    # conn.commit()

    totalString = "people are: "
    cursor.execute("SELECT * FROM Persons")
    for row in cursor.fetchall():
        print(row.FirstName, row.LastName)
        totalString += row.FirstName + " " + row.LastName + ", "
    return jsonify({"people": totalString})




if __name__ == '__main__':
    app.run()
