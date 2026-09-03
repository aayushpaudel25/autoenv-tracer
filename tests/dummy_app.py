import json
import sqlite3
import requests  # <-- Third-party package!

print(">> Dummy app is starting...")

# Fetch some data from the internet
response = requests.get("https://api.github.com")
print(f">> GitHub API Status: {response.status_code}")

with open("test_data.txt", "w") as f:
    f.write("Hello AutoEnv")

print(">> Dummy app finished.")