import requests
api_url = "http://127.0.0.1:5206/echo?msg=Hello"
response = requests.get(api_url)
val = response.json()
print(val.get("msg"))