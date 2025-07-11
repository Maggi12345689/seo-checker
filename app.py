from flask import Flask, request, jsonify, render_template
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/check-seo", methods=["POST"])
def check_seo():
    data = request.json
    html = data.get("html", "")
    soup = BeautifulSoup(html, "html.parser")
    results = {}

    def length_status(text, min_len, max_len):
        if len(text) < min_len:
            return "zu kurz"
        elif len(text) > max_len:
            return "zu lang"
        return "OK"

    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    results["Title"] = {
        "Status": "fehlt" if not title else length_status(title, 55, 65),
        "Details": f"{len(title)} Zeichen" if title else ""
    }

    desc_tag = soup.find("meta", attrs={"name": "description"})
    desc = desc_tag["content"].strip() if desc_tag and desc_tag.get("content") else ""
    results["Meta Description"] = {
        "Status": "fehlt" if not desc else length_status(desc, 118, 165),
        "Details": f"{len(desc)} Zeichen" if desc else ""
    }

    robots_tag = soup.find("meta", attrs={"name": "robots"})
    robots_content = robots_tag["content"].strip().lower() if robots_tag and robots_tag.get("content") else ""
    if not robots_content:
        robots_status = "fehlt"
    elif "index" in robots_content and "follow" in robots_content:
        robots_status = "ist indexiert, Links werden gefolgt"
    else:
        robots_status = "eingeschränkt"
    results["Meta Robots"] = {
        "Status": robots_status,
        "Details": robots_content
    }

    canonical = soup.find("link", rel="canonical")
    canonical_href = canonical["href"].strip() if canonical and canonical.get("href") else ""
    results["Canonical"] = {
        "Status": "fehlt" if not canonical_href else "vorhanden",
        "Details": canonical_href
    }

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

    images = soup.find_all("img")
    images_without_alt = [img for img in images if not img.get("alt")]
    img_status = "fehlt" if images_without_alt else "vorhanden"
    results["Bilder ALT-Attribute"] = {
        "Status": img_status,
        "Details": f"{len(images_without_alt)} ohne ALT" if images_without_alt else "alle Bilder mit ALT"
    }

    return jsonify(results)

@app.route("/check-meta", methods=["POST"])
def check_meta():
    data = request.json
    full_url = data.get("url", "").strip()
    results = {}

    if not full_url.startswith("http"):
        return jsonify({"error": "Ungültige URL"}), 400

    try:
        parsed = urlparse(full_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
    except:
        return jsonify({"error": "URL konnte nicht gelesen werden"}), 400

    # robots.txt prüfen
    try:
        robots_url = base_url + "/robots.txt"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(robots_url, timeout=10, headers=headers)
        if r.status_code == 200:
            results["robots.txt"] = {
                "Status": "Vorhanden",
                "Details": robots_url
            }
        else:
            results["robots.txt"] = {
                "Status": "Fehlt",
                "Details": f"Nicht gefunden (Status {r.status_code})"
            }
    except Exception as e:
        results["robots.txt"] = {
            "Status": "Fehler",
            "Details": f"Fehler beim Abruf: {str(e)}"
        }

    # Sitemap prüfen
    sitemap_urls = ["/sitemap.xml", "/sitemap_index.xml"]
    sitemap_found = False
    for sitemap_path in sitemap_urls:
        sitemap_full_url = base_url + sitemap_path
        try:
            s = requests.get(sitemap_full_url, timeout=10, headers=headers)
            if s.status_code == 200:
                results["Sitemap"] = {
                    "Status": "Vorhanden",
                    "Details": sitemap_full_url
                }
                sitemap_found = True
                break
        except:
            continue

    if not sitemap_found:
        results["Sitemap"] = {
            "Status": "Fehlt",
            "Details": "Keine Sitemap gefunden unter /sitemap.xml oder /sitemap_index.xml"
        }

    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)
