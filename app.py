from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup, Comment
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  

@app.route('/get-aqi-details', methods=['POST'])  
def get_aqi_details():
    data = request.get_json()
    url = data.get("url")

    if not url:
        return jsonify({"error": "URL is required"}), 400

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    result = {}

    # Breadcrumb path
    breadcrumb_items = soup.select("ol.breadcrumb li")
    result["breadcrumb"] = [item.text.strip() for item in breadcrumb_items]

    # Titles
    title = soup.select_one("div.detail-title h2")
    subtitle = soup.select_one("div.detail-title p")
    result["title"] = title.text.strip() if title else ""
    result["subtitle"] = subtitle.text.strip() if subtitle else ""

    # AQI level + color
    level = soup.select_one(".chart-box .level")
    level_color = level['style'].split("background:")[-1].strip() if level else ""
    level_text = level.text.strip() if level else ""
    result["aqi_level"] = level_text
    result["aqi_level_color"] = level_color

    # AQI number from commented HTML
    aqi_value = ""
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    for comment in comments:
        if 'class="indexValue"' in comment:
            comment_soup = BeautifulSoup(comment, 'html.parser')
            index_div = comment_soup.select_one(".indexValue")
            if index_div:
                aqi_value = index_div.text.strip()
                break
    result["aqi_value"] = aqi_value

    # Pollutants
    pollutants = {}
    for item in soup.select(".pollutants .pollutant-item"):
        name = item.select_one(".name").text.strip()
        value = item.select_one(".value").text.strip()
        pollutants[name] = value
    result["pollutants"] = pollutants

    # Weather
    weather = {}
    temp = soup.select_one(".temperature")
    hum = soup.select_one(".humidity")
    wind = soup.select_one(".wind")
    uv = soup.select_one(".uv")
    if temp: weather["temperature"] = temp.text.strip()
    if hum: weather["humidity"] = hum.text.strip()
    if wind: weather["wind"] = wind.text.strip()
    if uv: weather["uv"] = uv.text.strip()
    result["weather"] = weather

    # Included locations
    locations = []
    for loc in soup.select(".site-item"):
        loc_name = loc.select_one(".title").text.strip()
        loc_link = loc.get("href", "")
        locations.append({
            "location": loc_name,
            "link":  loc_link
        })
    result["included_places"] = locations

    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
