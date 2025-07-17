import requests

BASE_URL = "http://80.225.222.10:8080/"
HEADERS  = {"X-API-Key": "my-secret-token"}

def list_databases():
    params = {
        "query": "PRAGMA database_list;",
        "default_format": "JSONCompact"
    }
    resp = requests.get(BASE_URL, headers=HEADERS, params=params)
    resp.raise_for_status()
    return resp.json()

if __name__ == "__main__":
    dbs = list_databases()
    for row in dbs["data"]:
        print(f"Attached DB #{row[0]}: name={row[1]}, file={row[2]}")
