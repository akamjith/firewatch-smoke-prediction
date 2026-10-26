import math
import requests

def get_elevation(lat_list, lon_list):
    lat_str = ','.join(str(lat) for lat in lat_list)
    lon_str = ','.join(str(lon) for lon in lon_list)
    url = f"https://api.open-meteo.com/v1/elevation?latitude={lat_str}&longitude={lon_str}"
    response = requests.get(url)
    info = response.json()
    return info["elevation"]

def distance_km(lat1, lon1, lat2, lon2, elevation1, elevation2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    opposite = math.sin(dlat / 2) ** 2 +math.cos(lat1) * math.cos(lat2) * math.sin(dlon /2) ** 2
    hdistance = R * 2 * math.asin(math.sqrt(opposite))
    vdistance = abs(elevation2 - elevation1) / 1000
    return math.sqrt(hdistance**2 + vdistance**2)

def stablity_number(wind_speed_ms, day, cloudcover_percent):
    if day:
        if wind_speed_ms < 2:
            return "A"
        elif wind_speed_ms < 3:
            return "B"
        elif wind_speed_ms < 5:
            return "C"
        else: 
            return "D"
    else:
        if cloudcover_percent > 50: return "D"
        elif wind_speed_ms < 3: return "E"
        else: return "F"

def frp_factor(frp_firms):
    if frp_firms <= 0:
            return {"diameter": 2.0, "velocity": 1}

    burn_area = (frp_firms/1.2)
    fire_diameter = 2 * math.sqrt(burn_area / math.pi)

    d= max(min(fire_diameter, 500), 2.0)
    velocity = 1 + math.log10(frp_firms+1)
    v = max(min(velocity, 8),1)
    return {"d": round(d, 1), "v": round(v, 1)}


def get_atmosphere(lat, lon):
    pressure_levels = (1000, 975, 950, 925, 900, 850, 800, 700, 600, 500, 400, 300, 250, 200, 150, 100, 70, 50, 30)
    three_variables = ["boundary_layer_height"]

    for pressure in pressure_levels:
        three_variables.append(f"temperature_{pressure}hPa")
        three_variables.append(f"geopotential_height_{pressure}hPa")

    current = ",".join(three_variables)
    
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current={current}"
    atmosphere_response = requests.get(url)
    text = atmosphere_response.json()

    return text["current"]

def convert_celsius(text, pressure):
    temperature = text[f"temperature_{pressure}hPa"]
    temperature_kelvin = temperature + 273.15
    return temperature_kelvin

def n2(atmosphere, fire_elevation):
    pressure_levels = (
        1000, 975, 950, 925, 900, 850, 800, 700, 600,
        500, 400, 300, 250, 200, 150, 100, 70, 50, 30
    )

    target_height = fire_elevation + 2 * atmosphere["boundary_layer_height"]

    for i in range(len(pressure_levels) - 1):
        lower_pressure = pressure_levels[i]
        higher_pressure = pressure_levels[i + 1]

        lower_height = atmosphere[f"geopotential_height_{lower_pressure}hPa"]
        upper_height = atmosphere[f"geopotential_height_{higher_pressure}hPa"]
        if lower_height <= target_height <= upper_height:
            lower_temperature = convert_celsius(atmosphere, lower_pressure)
            upper_temperature = convert_celsius(atmosphere, higher_pressure)

            n_squared = brunt_vaisala_squared(
                lower_temperature,
                upper_temperature,
                lower_pressure,
                higher_pressure,
                lower_height,
                upper_height
            )

            return n_squared
    raise ValueError("Could not find pressure levels.")


def brunt_vaisala_squared(temp1_k, temp2_k, pressure1_hpa, pressure2_hpa, height1_m, height2_m):
    g = 9.81

    theta1 = temp1_k * (1000/pressure1_hpa) ** 0.286
    theta2 = temp2_k * (1000/pressure2_hpa) ** 0.286

    theta_avg = (theta1 + theta2) / 2
    dtheta_dz = (theta2 - theta1) / (height2_m - height1_m)

    return (g / theta_avg) * dtheta_dz

def plume_height(frp_firms, H_abl, brunt_vaisala_squared):
    fire_height = 0.24 * H_abl + 170 * frp_firms** 0.35 * math.exp(-0.6 * brunt_vaisala_squared/(2.5 * 10 ** -4))
    return fire_height


def wind_speed(lat,lon, fire_height):
    differences = []
    variables = []
    pressure_amount = (1000, 975, 950, 925, 900, 850, 800, 700, 600, 500, 400, 300, 250, 200, 150, 100, 70, 50, 30)
    elev = get_elevation([lat], [lon])[0]
    final_elevation =  elev + fire_height
    for pressure in pressure_amount:
        variables.append(f"wind_speed_{pressure}hPa")
        variables.append(f"geopotential_height_{pressure}hPa")
    current = ",".join(variables)
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current={current}"
    answer = requests.get(url)
    data = answer.json()
    for pressure in pressure_amount:
        height = data["current"][f"geopotential_height_{pressure}hPa"]
        difference = abs(final_elevation - height)
        differences.append((difference, pressure))
    smallest = min(differences)
    meteo_pressure = smallest[1]
    wind = data["current"][f"wind_speed_{meteo_pressure}hPa"]
    return wind

def calculate_plume_height(lat, lon, frp):
    atmosphere = get_atmosphere(lat, lon)
    H_abl = atmosphere["boundary_layer_height"]
    fire_elevation = get_elevation([lat], [lon])[0]
    n_squared = n2(atmosphere, fire_elevation)
    fire_height = plume_height(frp, H_abl, n_squared)
    return fire_height