from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from geo_math import wind_speed, calculate_plume_height
import requests
import csv
import io
import math
import os

load_dotenv()  

app = Flask(__name__)
CORS(app)

FIRMS_MAP_KEY = os.environ.get("FIRMS_MAP_KEY")
print("Key loaded:", FIRMS_MAP_KEY[:6] + "..." if FIRMS_MAP_KEY else "MISSING")
@app.route("/api/hello")
def hello():
    return jsonify({"message": "Backend is alive!"})


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def bearing_deg(lat1, lon1, lat2, lon2):
    lat1, lat2 = math.radians(lat1), math.radians(lat2)
    dlon = math.radians(lon2 - lon1)
    y = math.sin(dlon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


@app.route("/api/fires")
def get_fires():
    lat = float(request.args.get("lat"))
    lon = float(request.args.get("lon"))
    radius_km = float(request.args.get("radius_km", 200))
    days = int(request.args.get("days", 2))


    lat_pad = radius_km / 111
    lon_pad = radius_km / (111 * math.cos(math.radians(lat)))
    west, east = lon - lon_pad, lon + lon_pad
    south, north = lat - lat_pad, lat + lat_pad

    sensor = "VIIRS_SNPP_NRT"
    url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{FIRMS_MAP_KEY}/{sensor}/{west},{south},{east},{north}/{days}"

    response = requests.get(url)
    reader = csv.DictReader(io.StringIO(response.text))
    print("FIRMS status:", response.status_code)
    print("FIRMS response:", response.text[:500])

    fires = []
    for row in reader:
        flat = float(row["latitude"])
        flon = float(row["longitude"])
        distance = haversine_km(lat, lon, flat, flon)
        if distance <= radius_km:
            frp = float(row["frp"])

            fire_height = calculate_plume_height(flat, flon, frp,)

            fire_wind = wind_speed(flat, flon, fire_height)
            fires.append({
             "lat": flat,
             "lon": flon,
            "distance_km": round(distance, 1),
            "bearing_fire_to_user": round(bearing_deg(flat, flon, lat, lon)),
            "confidence": row.get("confidence"),
            "acq_date": row.get("acq_date"),
            "acq_time": row.get("acq_time"),
            "frp": row.get("frp"),
            "plume_height": round(fire_height, 1),
            "fire_speed": round(fire_wind, 1),
})

    fires.sort(key=lambda f: f["distance_km"])
    return jsonify({"fires": fires, "count": len(fires)})


if __name__ == "__main__":
    app.run(port=5000, debug=True)
