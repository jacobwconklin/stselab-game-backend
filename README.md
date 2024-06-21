## Deployment
Deployed through Azure, currently live at:
https://stselab-games-backend.azurewebsites.net/

To deploy do the following:

(Make sure all .sql files are included in "appService.zipIgnorePattern" in settings.json in the .vscode folder. 
Deploying the app with sql files caused issues before.)

1) Make sure you are added to the Azure Subscription as a contributor

2) Install Azure Tools extension pack in VS Code. (if not installed already)

3) ALWAYS RUN
```
git pull
```
BEFORE DEPLOYING (in case other contributor / team has made necessary changes) and test version before deploying. 

4) Push changes to GIT. Either in terminal or using VSCode. This is so that your changes persist if another team deploys 

5) In VS Code with the backend folder opened click:
    View -> Command Palette -> Azure App Service: Deploy to Web App

Done.

# Running Locally

```
Denotes code to run on bash terminal (not sure if adjustments needed for Windows Powershell)
```

## First time:
1) Create file in the same level as app.py named 'environmentSecrets.py'.
In this file add the following lines: 
AZURE_SQL_CONNECTION_STRING = 'database connection string'
    where database connection string connects to stselab-games-data Azure SQL Database
VT_MYSQL_HOST = 'host ip address'
    where host ip address is the ip of the VT MySQL server
VT_MYSQL_PORT = 'port number'
    where port number is the port number of the VT MySQL server
VT_MYSQL_DB = 'database name'
    where database name is the name of the VT MySQL database
VT_MYSQL_USER = 'database username'
    where database username is the username for the VT MySQL database
VT_MYSQL_PASSWORD = 'database password'
    where database password is the password for the VT MySQL database

2) Install Python if not already installed on machine

3) Create a python virtual environment with
```
python -m venv .venv
```

4) Activate and use that environment with
```
source .venv/Scripts/activate
```

5) Install all requirements with 
```
pip install -r requirements.txt
```

6) To run locally and update whenever changes are saved run the command:
```
flask --app app.py --debug run
```

7) Local backend will be accessible at:
http://127.0.0.1:5000


## Already have .venv
1) Make sure to source the environment again whenever returning.
```
source .venv/Scripts/activate
```

2) Then run locally:
```
flask --app app.py --debug run
```

# Note about sensitive information:

1) Do NOT push any API keys or database connection strings to GitHub, this application is in a public repository. 
Use the .gitignore file to specify files you do not want to push to GitHub.

2) Do NOT deploy any .sql files. Not sure why, but this has caused issues with the deployed server before. 
Use .vscode/settings.json to specify files that will not be deployed to Azure. Also, environmentSecrets.py is set up 
to hold sensitive information that is not wanted on GitHub but that IS needed for deployment. This was easier to access than
.env files, so I used this system. It is essentially serving as a .env or .yaml file for deployment secrets.

# Deploy a Python (Flask) web app to Azure App Service - Sample Application

This is the sample Flask application for the Azure Quickstart [Deploy a Python (Django or Flask) web app to Azure App Service](https://docs.microsoft.com/en-us/azure/app-service/quickstart-python). For instructions on how to create the Azure resources and deploy the application to Azure, refer to the Quickstart article.

Sample applications are available for the other frameworks here:

* Django [https://github.com/Azure-Samples/msdocs-python-django-webapp-quickstart](https://github.com/Azure-Samples/msdocs-python-django-webapp-quickstart)
* FastAPI [https://github.com/Azure-Samples/msdocs-python-fastapi-webapp-quickstart](https://github.com/Azure-Samples/msdocs-python-fastapi-webapp-quickstart)

If you need an Azure account, you can [create one for free](https://azure.microsoft.com/en-us/free/).
