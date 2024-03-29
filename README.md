## Deployment
Deployed through Azure, currently live at:
https://stse-backend.azurewebsites.net/

# Running Locally

```
Denotes code to run on bash terminal (not sure if adjustments needed for Windows Powershell)
```

## First time:
1) Create file in the same level as app.py named 'environmentSecrets.py'.
In this file add the line: AZURE_SQL_CONNECTION_STRING = 'database connection string'
where database connection 


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

# Deploy a Python (Flask) web app to Azure App Service - Sample Application

This is the sample Flask application for the Azure Quickstart [Deploy a Python (Django or Flask) web app to Azure App Service](https://docs.microsoft.com/en-us/azure/app-service/quickstart-python). For instructions on how to create the Azure resources and deploy the application to Azure, refer to the Quickstart article.

Sample applications are available for the other frameworks here:

* Django [https://github.com/Azure-Samples/msdocs-python-django-webapp-quickstart](https://github.com/Azure-Samples/msdocs-python-django-webapp-quickstart)
* FastAPI [https://github.com/Azure-Samples/msdocs-python-fastapi-webapp-quickstart](https://github.com/Azure-Samples/msdocs-python-fastapi-webapp-quickstart)

If you need an Azure account, you can [create one for free](https://azure.microsoft.com/en-us/free/).
