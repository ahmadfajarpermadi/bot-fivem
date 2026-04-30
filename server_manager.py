import json
import requests

CONFIG_FILE = "config.json"
def load_servers():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)["servers"]
    
def save_servers(servers):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"servers": servers}, f, indent=4)

def get_players_cfx(join_code):
    try:
        url = f"https://servers-frontend.fivem.net/api/servers/single/{join_code}"
        res = requests.get(url, timeout=5)
        data = res.json()

        info = data["Data"]
        players = info["players"]

        banner = info.get("vars", {}).get("banner_detail")

        return players, info

    except Exception as e:
        print("Error:", e)
        return None, None