
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

    def length_status(text, min_len, max_len):
        if len(text) < min_len: return "Zu kurz"
        elif len(text) > max_len: return "Zu lang"
        return "OK"

    # Title
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    results["Title"] = {
        "Status": "Fehlt" if not title else length_status(title, 30, 60),
        "Details": f"{len(title)} Zeichen" if title else ""
    }

    # Meta Description
    desc_tag = soup.find("meta", attrs={"name": "description"})
    desc = desc_tag["content"].strip() if desc_tag and desc_tag.get("content") else ""
    results["Meta Description"] = {
        "Status": "Fehlt" if not desc else length_status(desc, 70, 160),
        "Details": f"{len(desc)} Zeichen" if desc else ""
    }

    # H1
    h1s = soup.find_all("h1")
    results["H1"] = {
        "Status": "Fehlt" if not h1s else "Mehrere H1" if len(h1s) > 1 else "OK",
        "Details": f"{len(h1s)} gefunden"
    }

    # Images without alt
    images = soup.find_all("img")
    no_alt = [img for img in images if not img.get("alt")]
    results["Bilder ohne ALT"] = {
        "Status": "OK" if not no_alt else f"{len(no_alt)} ohne ALT",
        "Details": ""
    }

    # Canonical
    canonical = soup.find("link", rel="canonical")
    canonical_href = canonical["href"] if canonical and canonical.get("href") else ""
    results["Canonical"] = {
        "Status": "Fehlt" if not canonical_href else "OK",
        "Details": canonical_href
    }

    # HTML lang
    html_tag = soup.find("html")
    lang = html_tag.get("lang") if html_tag else None
    results["HTML lang"] = {
        "Status": "Fehlt" if not lang else "OK",
        "Details": lang or ""
    }

    # robots.txt
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
