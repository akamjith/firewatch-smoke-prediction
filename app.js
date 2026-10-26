const button = document.getElementById('locate-btn');
const output = document.getElementById('output');
const aqiOutput = document.getElementById('aqi-output');

const form = document.getElementById('manual-form');
const latInput = document.getElementById('lat-input');
const lonInput = document.getElementById('lon-input');

let map;
let fireLayer;

async function handleLocation(lat, lon) {
    output.textContent = `You're at ${lat}, ${lon}`;
    getAirQuality(lat, lon);
    showMap(lat, lon);

    const wind = await getWindData(lat, lon);
    console.log('Wind:', wind);

    getFires(lat, lon, wind);
}

function handleClick() {
    output.textContent = 'Locating...';

    navigator.geolocation.getCurrentPosition(
        (position) => {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            handleLocation(lat, lon);
        },
        (error) => {
            output.textContent = `Error: ${error.message}`;
        }
    );
}

button.addEventListener('click', handleClick);

form.addEventListener('submit', (event) => {
    event.preventDefault();

    const lat = parseFloat(latInput.value);
    const lon = parseFloat(lonInput.value);

    handleLocation(lat, lon);
});

async function getAirQuality(lat, lon) {
    try {
        const url = `https://air-quality-api.open-meteo.com/v1/air-quality?latitude=${lat}&longitude=${lon}&current=us_aqi,pm2_5,pm10`;
        const response = await fetch(url);
        const data = await response.json();

        const aqi = data.current.us_aqi;
        const pm25 = data.current.pm2_5;

        aqiOutput.textContent = `Air quality: AQI ${aqi}, PM2.5 ${pm25} µg/m³`;

        if (aqi <= 50) {
            alert('Air quality is good.');
        } else if (aqi <= 100) {
            alert('Air quality is moderate.');
        } else if (aqi <= 150) {
            alert('Air quality is unhealthy for sensitive groups.');
        } else if (aqi <= 200) {
            alert('Air quality is unhealthy.');
        } else if (aqi <= 300) {
            alert('Air quality is very unhealthy.');
        } else {
            alert('Air quality is hazardous.');
        }
    } catch (error) {
        aqiOutput.textContent = "Error fetching air quality data.";
        console.error(error);
    }
}

function showMap(lat, lon) {
    if (map) {
        map.setView([lat, lon], 10);
    } else {
        map = L.map('map').setView([lat, lon], 10);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap contributors',
        }).addTo(map);
    }

    L.marker([lat, lon])
        .addTo(map)
        .bindPopup('You are here');
}

function calculateBearing(lat1, lon1, lat2, lon2) {
    const toRad = (deg) => (deg * Math.PI) / 180;
    const toDeg = (rad) => (rad * 180) / Math.PI;

    const dLon = toRad(lon2 - lon1);

    const y = Math.sin(dLon) * Math.cos(toRad(lat2));

    const x =
        Math.cos(toRad(lat1)) * Math.sin(toRad(lat2)) -
        Math.sin(toRad(lat1)) *
            Math.cos(toRad(lat2)) *
            Math.cos(dLon);

    const bearing = toDeg(Math.atan2(y, x));

    return (bearing + 360) % 360;
}

function angularDifference(angle1, angle2) {
    const diff = Math.abs(angle1 - angle2) % 360;
    return diff > 180 ? 360 - diff : diff;
}

async function getFires(lat, lon, wind) {
    output.textContent = 'Searching for fires...';

    const url = `http://127.0.0.1:5000/api/fires?lat=${lat}&lon=${lon}&radius_km=75&days=3`;

    try {
        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`Fire request failed: ${response.status}`);
        }

        const data = await response.json();

        console.log('Fires found:', data.fires.length, data.fires);

        if (fireLayer) {
            fireLayer.clearLayers();
        } else {
            fireLayer = L.layerGroup().addTo(map);
        }

        const smokeDirection = (wind.direction + 180) % 360;

        data.fires.forEach((fire) => {
            const bearingToUser = calculateBearing(
                fire.lat,
                fire.lon,
                lat,
                lon
            );

            const diff = angularDifference(
                smokeDirection,
                bearingToUser
            );

            const fireWindSpeed = Number(fire.fire_speed);

            let etaHours = null;

            if (diff <= 30 && fireWindSpeed > 0) {
                etaHours = fire.distance_km / fireWindSpeed;

                console.log(
                    `⚠️ RISK — fire at ${fire.distance_km}km, ` +
                    `plume wind ${fireWindSpeed} km/h, ` +
                    `smoke ETA ~${etaHours.toFixed(1)} hrs`
                );
            } else {
                console.log(
                    `Fire at ${fire.distance_km}km — smoke not heading your way ` +
                    `(off by ${diff.toFixed(0)}°)`
                );
            }

            const threatScore = Math.round(
                100 * (1 - fire.distance_km / 75)
            );

            let popup =
                `${fire.distance_km} km away<br>` +
                `Detected: ${fire.acq_date} ${fire.acq_time}<br>` +
                `FRP: ${fire.frp} MW<br>` +
                `Plume height: ${fire.plume_height} m<br>` +
                `Wind at plume: ${fireWindSpeed.toFixed(1)} km/h<br>` +
                `Threat score: ${threatScore}/100`;

            if (etaHours !== null) {
                popup += `<br><strong>⚠️ Smoke ETA: ~${etaHours.toFixed(1)} hrs</strong>`;
            }

            L.circleMarker([fire.lat, fire.lon], {
                radius: 6,
                color: etaHours !== null ? 'orange' : 'red',
                fillOpacity: 0.8,
            })
                .bindPopup(popup)
                .addTo(fireLayer);
        });

        output.textContent = `Found ${data.fires.length} fires.`;

    } catch (error) {
        output.textContent = 'Error searching for fires.';
        console.error(error);
    }
}

async function getWindData(lat, lon) {
    const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=wind_speed_10m,wind_direction_10m&wind_speed_unit=kmh`;

    const response = await fetch(url);
    const data = await response.json();

    return {
        speed: data.current.wind_speed_10m,
        direction: data.current.wind_direction_10m,
    };
}