# Fire Watch

**A wildfire and smoke awareness application that uses satellite detections, weather data, and atmospheric formulas to estimate potential smoke movement.**

## About the Project

Fire Watch is a project created for the Congressional App Challenge. It was inspired by the poor air quality caused by wildfires and the impact smoke can have on communities far from where a fire is burning.

The goal of Fire Watch is to help users understand nearby wildfire activity, view current air quality information, and explore where smoke might travel based on wind conditions.

## Features

- **Wildfire Detection:** Retrieves satellite-detected fire data from NASA FIRMS using the VIIRS Suomi NPP Near Real-Time dataset.
- **Interactive Map:** Displays nearby fire detections and the user's selected location using Leaflet.
- **Air Quality Information:** Retrieves current US AQI, PM2.5, and PM10 data from Open-Meteo.
- **Plume Height Estimation:** Uses fire radiative power, atmospheric boundary layer height, and a Brunt–Väisälä stability calculation to estimate potential plume height.
- **Wind Analysis:** Uses weather data at an estimated plume altitude to examine wind conditions near detected fires.
- **Smoke Arrival Estimates:** Compares wind direction with the direction toward the user's location and calculates a rough potential smoke arrival time when the wind appears aligned.
- **Location Selection:** Allows users to use their browser's location or manually enter latitude and longitude.

## Technologies Used

- **Python** — Backend logic and atmospheric calculations
- **Flask** — Local backend and API endpoints
- **JavaScript** — Frontend functionality and data processing
- **HTML and CSS** — User interface
- **Leaflet** — Interactive map
- **NASA FIRMS** — Satellite fire detection data
- **Open-Meteo** — Weather, atmospheric, elevation, and air quality data
- **Brunt–Väisälä formula** — Atmospheric stability calculation used in the plume height estimation

## How It Works

1. The user selects a location.
2. The frontend retrieves air quality and local wind information.
3. The Flask backend requests recent fire detections from NASA FIRMS and filters them by distance.
4. Atmospheric and elevation data from Open-Meteo are used in calculations that estimate plume height and select relevant wind conditions.
5. The frontend displays fire detections on the map and uses the estimated wind direction and speed to identify fires whose smoke might be traveling toward the selected location.

## Running Fire Watch Locally

### Requirements

- Python 3
- A NASA FIRMS map key
- An internet connection

### 1. Install the Python dependencies

Open a terminal in the project directory and run:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install flask flask-cors python-dotenv requests
```

### 2. Configure your NASA FIRMS key

Create a local file named `.env` in the project directory:

```env
FIRMS_MAP_KEY=your_actual_firms_map_key
```

Replace the placeholder with your own key from NASA FIRMS.

**Do not upload your `.env` file or expose your API key in the public repository.**

### 3. Start the backend

In the project directory, run:

```bash
python3 app.py
```

The Flask backend runs locally at:

```text
http://127.0.0.1:5000
```

### 4. Open the frontend

Open a second terminal in the project directory and run:

```bash
python3 -m http.server 8000
```

Then visit:

```text
http://localhost:8000
```

Make sure `index.html`, `app.js`, `app.py`, and `geo_math.py` are in the appropriate project locations. Keep the Flask backend running while using the application.

## Limitations and Responsible Use

Fire Watch is an experimental project intended to help users explore wildfire activity, air quality, and potential smoke movement.

Its plume height calculations and smoke arrival estimates are simplified approximations. They do not fully model atmospheric dispersion, changing weather conditions, terrain, or the complex behavior of actual wildfire smoke. The estimated arrival time should not be interpreted as a reliable prediction.

Fire Watch is not an official emergency alert system and should not be used as the sole source of information for evacuation decisions or firefighter safety. Always follow official emergency instructions and local air quality advisories.

## Acknowledgments

- NASA FIRMS for satellite fire detection data
- Open-Meteo for weather, atmospheric, elevation, and air quality data
- Leaflet for interactive mapping
- The open-source community for the tools and libraries used in this project
