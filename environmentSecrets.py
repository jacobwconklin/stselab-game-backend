import os
from dotenv import load_dotenv

load_dotenv()
print("TEST")

def required(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required setting: {name}")
    return value

VT_MYSQL_HOST = required('VT_MYSQL_HOST')
VT_MYSQL_PORT = required('VT_MYSQL_PORT')
VT_MYSQL_STSELAB_DB = required('VT_MYSQL_STSELAB_DB')
VT_MYSQL_USER = required('VT_MYSQL_USER')
VT_MYSQL_PASSWORD = required('VT_MYSQL_PASSWORD')
VT_MYSQL_DESIGN_PROCESS_DB = required('VT_MYSQL_DESIGN_PROCESS_DB')
VT_MYSQL_PASSWORD_SALT = required('VT_MYSQL_PASSWORD_SALT')
ADMIN_EMAIL_PASSWORD = os.getenv('ADMIN_EMAIL_PASSWORD')