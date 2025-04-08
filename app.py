from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright

app = Flask(__name__)

@app.route("/upgrades", methods=["GET"])
def get_upgrades():
    eq_class = request.args.get("class", "Bard")
    slot = request.args.get("slot", "Head")
    ac = request.args.get("ac", "0")
    hp = request.args.get("hp", "0")

    url = f"https://www.raidloot.com/items?class={eq_class}&slot={slot}&ac={ac}&hp={hp}"

   with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)", viewport={"width": 1280, "height": 720})
    page = context.new_page()

    try:
        page.goto(url, timeout=60000)
        page.wait_for_timeout(3000)  # wait for 3 seconds to allow JS to load
        page.wait_for_selector("table.table", timeout=20000)
        html = page.inner_html("table.table")
    except Exception as e:
        page.screenshot(path="error.png")  # optional: save for debugging
        browser.close()
        return jsonify({"error": f"Timeout or error: {str(e)}"})
    
    browser.close()
       
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    items = []

    for row in soup.find_all("tr")[1:]:
        cols = row.find_all("td")
        if len(cols) < 5:
            continue
        name = cols[0].text.strip()
        link = "https://www.raidloot.com" + cols[0].find("a")["href"]
        ac_val = cols[1].text.strip()
        hp_val = cols[2].text.strip()
        heroics = cols[4].text.strip()

        items.append({
            "name": name,
            "link": link,
            "ac": ac_val,
            "hp": hp_val,
            "heroics": heroics
        })

    return jsonify(items)

@app.route("/")
def index():
    return "Raidloot Scraper with Playwright is running!"

import os
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
