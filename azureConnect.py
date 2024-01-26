import pyodbc as odbc
import os
from dotenv import load_dotenv
load_dotenv()

connection_string = os.getenv('AZURE_SQL_CONNECTIONSTRING')

conn = odbc.connect(connection_string)

cursor = conn.cursor()

cursor.execute(f"INSERT INTO Persons (FirstName, LastName) VALUES (?, ?)", "lim", "Kob")
conn.commit()

cursor.execute("SELECT * FROM Persons")

for row in cursor.fetchall():
    print(row.FirstName, row.LastName)