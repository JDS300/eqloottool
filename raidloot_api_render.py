
from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

BASE_URL = "https://www.raidloot.com/items"

def extract_items(html):
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="table")
    if not table:
        return []

    items = []
    rows = table.find_all("tr")[1:]  # skip header row
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 5:
            continue

        item_link = cols[0].find("a")
        item_name = item_link.text.strip() if item_link else "Unknown"
        link = "https://www.raidloot.com" + item_link['href'] if item_link else ""
        ac = cols[1].text.strip()
        hp = cols[2].text.strip()
        heroics = cols[4].text.strip()

        items.append({
            "name": item_name,
            "link": link,
            "ac": ac,
            "hp": hp,
            "heroics": heroics
        })
    return items

@app.route("/upgrades", methods=["GET"])
def get_upgrades():
    eq_class = request.args.get("class", "Bard")
    slot = request.args.get("slot", "")
    ac = request.args.get("ac", "")
    hp = request.args.get("hp", "")
    hsta = request.args.get("hsta", "")
    atk = request.args.get("atk", "")
    source = request.args.get("source", "")

    params = {
        "class": eq_class,
        "slot": slot,
        "ac": ac,
        "hp": hp,
        "hsta": hsta,
        "atk": atk,
        "source": source
    }

    try:
        resp = requests.get(BASE_URL, params=params)
        items = extract_items(resp.text)
        return jsonify(items)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    return "Raidloot Upgrade API is running!"

import os
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
