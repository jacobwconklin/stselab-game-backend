from flask import request
import requests

simulationUrl = 'http://64.23.136.232/date/'

def playDrive():
    data = request.json
    result = requests.post(simulationUrl + 'playDrive', json=data)
    return result.json()

def playLong():
    data = request.json
    result = requests.post(simulationUrl + 'playLong', json=data)
    return result.json()

def playFairway():
    data = request.json
    result = requests.post(simulationUrl + 'playFairway', json=data)
    return result.json()

def playShort():
    data = request.json
    result = requests.post(simulationUrl + 'playShort', json=data)
    return result.json()

def playPutt():
    data = request.json
    result = requests.post(simulationUrl + 'playPutt', json=data)
    return result.json()

def h_arch():
    data = request.json
    result = requests.post(simulationUrl + 'h_arch', json=data)
    return result.json()

def lp_arch():
    data = request.json
    result = requests.post(simulationUrl + 'lp_arch', json=data)
    return result.json()

def dap_arch():
    data = request.json
    result = requests.post(simulationUrl + 'dap_arch', json=data)
    return result.json()

def ds_arch():
    data = request.json
    result = requests.post(simulationUrl + 'ds_arch', json=data)
    return result.json()