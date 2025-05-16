from flask import Flask, request, jsonify, render_template
from bs4 import BeautifulSoup
import requests

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/check-seo", methods=["POST"])
def check_seo():
    data = request.json
    html = data.get("html", "")
    url = data.get("url", None)

    soup = BeautifulSoup(html, "html.parser")
    results = {}

    # Hilfsfunktion zur Längenprüfung
    def length_status(text, min_len, max_len):
        if len(text) < min_len:
            return "Zu kurz"
        elif len(text) > max_len:
            return "Zu lang"
        return "OK"

    # --- Title ---
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    results["Title"] = {
        "Status": "fehlt" if not title else length_status(title, 55, 65),
        "Details": f"{len(title)} Zeichen" if title else ""
    }

    # --- Meta Description ---
    desc_tag = soup.find("meta", attrs={"name": "description"})
    desc = desc_tag["content"].strip() if desc_tag and desc_tag.get("content") else ""
    results["Meta Description"] = {
        "Status": "fehlt" if not desc else length_status(desc, 118, 165),
        "Details": f"{len(desc)} Zeichen" if desc else ""
    }

    # --- Meta Robots ---
    robots_tag = soup.find("meta", attrs={"name": "robots"})
    robots_content = robots_tag["content"].strip().lower() if robots_tag and robots_tag.get("content") else ""
    if not robots_content:
        robots_status = "fehlt"
    elif "index" in robots_content and "follow" in robots_content:
        robots_status = "ist indexiert, Links wird gefolgt"
    else:
        robots_status = "fehlt"
    results["Meta Robots"] = {
        "Status": robots_status,
        "Details": robots_content
    }

    # --- Canonical ---
    canonical = soup.find("link", rel="canonical")
    canonical_href = canonical["href"].strip() if canonical and canonical.get("href") else ""
    results["Canonical"] = {
        "Status": "fehlt" if not canonical_href else "vorhanden",
        "Details": canonical_href
    }

    # --- H1 ---
    h1s = soup.find_all("h1")
    if not h1s:
        h1_status = "fehlt"
    elif len(h1s) == 1:
        h1_status = "vorhanden"
    else:
        h1_status = "mehrfach definiert"
    results["H1"] = {
        "Status": h1_status,
        "Details": f"{len(h1s)} gefunden"
    }

    # --- Bilder mit ALT ---
    images = soup.find_all("img")
    images_without_alt = [img for img in images if not img.get("alt")]
    img_status = "fehlt" if images_without_alt else "vorhanden"
    results["Bilder ALT-Attribute"] = {
        "Status": img_status,
        "Details": f"{len(images_without_alt)} ohne ALT" if images_without_alt else ""
    }

    # --- robots.txt ---
    if url:
        try:
            domain = url.split("/")[2]
            robots = requests.get(f"https://{domain}/robots.txt", timeout=5).text
            results["robots.txt"] = {
                "Status": "OK" if "User-agent" in robots else "Leer/Fehlt",
                "Details": robots[:150] + "..." if len(robots) > 150 else robots
            }
        except:
            results["robots.txt"] = {
                "Status": "Nicht erreichbar",
                "Details": ""
            }

    return jsonify(results)
