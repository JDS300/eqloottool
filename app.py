from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import os

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
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()

        try:
            page.goto(url, timeout=60000)
            page.wait_for_timeout(3000)
            page.wait_for_selector("table.items.floating-header", timeout=20000)
            html = page.inner_html("table.items.floating-header")
        except Exception as e:
            page.screenshot(path="error.png")
            browser.close()
            return jsonify({"error": f"Timeout or error: {str(e)}"})

        browser.close()

    soup = BeautifulSoup(html, "html.parser")
    items = []

    for row in soup.find_all("tr")[1:]:
        cols = row.find_all("td")
        if len(cols) < 12:
            continue

        link_tag = cols[1].find("a")
        name = link_tag.text.strip() if link_tag else cols[1].text.strip()
        link = "https://www.raidloot.com" + link_tag["href"] if link_tag else ""

        item = {
            "name": name,
            "link": link,
            "type": cols[2].text.strip(),
            "score": cols[3].text.strip(),
            "ac": cols[4].text.strip(),
            "hp": cols[5].text.strip(),
            "atk": cols[6].text.strip(),
            "hsta": cols[7].text.strip(),
            "hagi": cols[8].text.strip(),
            "hdex": cols[9].text.strip(),
            "hstr": cols[10].text.strip(),
            "source": cols[11].text.strip()
        }

        items.append(item)

    return jsonify(items)
    
@app.route("/search", methods=["GET"])
def search_item_by_name():
    item_name = request.args.get("name", "")
    if not item_name:
        return jsonify({"error": "Missing 'name' parameter"}), 400

    search_url = f"https://www.raidloot.com/items?name={item_name.replace(' ', '+')}&view=Table"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()

        try:
            page.goto(search_url, timeout=60000)
            page.wait_for_timeout(3000)

            if page.query_selector("table.items"):
                page.wait_for_selector("table.items", timeout=20000)
                html = page.inner_html("table.items")
                soup = BeautifulSoup(html, "html.parser")

                items = []
                for row in soup.find_all("tr")[1:]:
                    cols = row.find_all("td")
                    if len(cols) < 12:
                        continue

                    link_tag = cols[1].find("a")
                    name = link_tag.text.strip() if link_tag else cols[1].text.strip()
                    link = "https://www.raidloot.com" + link_tag["href"] if link_tag else ""

                    item = {
                        "name": name,
                        "link": link,
                        "type": cols[2].text.strip(),
                        "score": cols[3].text.strip(),
                        "ac": cols[4].text.strip(),
                        "hp": cols[5].text.strip(),
                        "atk": cols[6].text.strip(),
                        "hsta": cols[7].text.strip(),
                        "hagi": cols[8].text.strip(),
                        "hdex": cols[9].text.strip(),
                        "hstr": cols[10].text.strip(),
                        "source": cols[11].text.strip()
                    }
                    items.append(item)

                return jsonify(items[:3])

            else:
                page.wait_for_selector("div.item", timeout=20000)
                html = page.content()
                soup = BeautifulSoup(html, "html.parser")

                item_div = soup.find("div", class_="item")
                if not item_div:
                    return jsonify({"error": "Item div not found"}), 404

                name_tag = item_div.find("span", class_="itemname")
                name = name_tag.text.strip() if name_tag else item_name
                link_tag = item_div.find("a", class_="itemlink")
                link = "https://www.raidloot.com" + link_tag["href"] if link_tag else ""

                def get_stat(soup, label):
                    label_tag = soup.find("label", string=label)
                    if label_tag and label_tag.find_next_sibling("span"):
                        return label_tag.find_next_sibling("span").text.strip()
                    return ""

                item = {
                    "name": name,
                    "link": link,
                    "type": item_div.find("span", class_="note").text.strip() if item_div.find("span", class_="note") else "",
                    "score": "",
                    "ac": get_stat(item_div, "AC:"),
                    "hp": get_stat(item_div, "HP:"),
                    "atk": get_stat(item_div, "ATK:"),
                    "hsta": get_stat(item_div, "STA:"),
                    "hagi": get_stat(item_div, "AGI:"),
                    "hdex": get_stat(item_div, "DEX:"),
                    "hstr": get_stat(item_div, "STR:"),
                    "source": ""
                }

                return jsonify([item])

        except Exception as e:
            browser.close()
            return jsonify({"error": f"Timeout or error: {str(e)}"}), 500

        browser.close()

@app.route("/")
def index():
    return "Raidloot Scraper with Playwright is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)

