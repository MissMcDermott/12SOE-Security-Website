import json
import requests



appUrl = "http://127.0.0.1:5000/retrieve"
with requests.get(appUrl, auth=("Test", "123")) as response:
    print(json.loads(response.content))

