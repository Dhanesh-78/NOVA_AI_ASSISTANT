import requests


# ============================================================
# WEATHER SERVICE
# ============================================================

def get_weather(city: str):

    city = city.strip()

    if not city:
        return {
            "success": False,
            "message": "Please tell me the city name."
        }

    try:

        # ====================================================
        # STEP 1: FIND CITY COORDINATES
        # ====================================================

        geo_url = "https://geocoding-api.open-meteo.com/v1/search"

        print(f"\nSearching location: {city}")

        geo_response = requests.get(
            geo_url,
            params={
                "name": city,
                "count": 5,
                "language": "en",
                "format": "json"
            },
            timeout=15
        )

        print("Geocoding status:", geo_response.status_code)

        geo_response.raise_for_status()

        geo_data = geo_response.json()

        results = geo_data.get("results", [])

        # ====================================================
        # FALLBACK FOR LOCATIONS LIKE:
        # "Nerul Navi Mumbai"
        # ====================================================

        if not results:

            # Try only the first part of the location
            # Example:
            # Nerul Navi Mumbai -> Nerul
            simplified_city = city.split()[0]

            if simplified_city.lower() != city.lower():

                print(
                    f"No exact result. Trying: {simplified_city}"
                )

                geo_response = requests.get(
                    geo_url,
                    params={
                        "name": simplified_city,
                        "count": 5,
                        "language": "en",
                        "format": "json"
                    },
                    timeout=15
                )

                print(
                    "Fallback geocoding status:",
                    geo_response.status_code
                )

                geo_response.raise_for_status()

                geo_data = geo_response.json()

                results = geo_data.get(
                    "results",
                    []
                )

        # ====================================================
        # LOCATION NOT FOUND
        # ====================================================

        if not results:

            return {
                "success": False,
                "message": (
                    f"I couldn't find the location {city}."
                )
            }

        # ====================================================
        # SELECT LOCATION
        # ====================================================

        location = results[0]

        latitude = location.get("latitude")
        longitude = location.get("longitude")

        location_name = location.get(
            "name",
            city
        )

        country = location.get(
            "country",
            ""
        )

        admin1 = location.get(
            "admin1",
            ""
        )

        # ====================================================
        # SAFETY CHECK
        # ====================================================

        if latitude is None or longitude is None:

            return {
                "success": False,
                "message": (
                    "I found the location, "
                    "but couldn't get its coordinates."
                )
            }

        print(
            f"Location found: {location_name}, "
            f"{admin1}, {country}"
        )

        print(
            f"Coordinates: {latitude}, {longitude}"
        )

        # ====================================================
        # STEP 2: GET CURRENT WEATHER
        # ====================================================

        weather_url = (
            "https://api.open-meteo.com/v1/forecast"
        )

        weather_response = requests.get(
            weather_url,
            params={
                "latitude": latitude,
                "longitude": longitude,

                "current": (
                    "temperature_2m,"
                    "relative_humidity_2m,"
                    "apparent_temperature,"
                    "precipitation,"
                    "weather_code,"
                    "wind_speed_10m"
                ),

                "timezone": "auto"
            },

            timeout=15
        )

        print(
            "Weather API status:",
            weather_response.status_code
        )

        weather_response.raise_for_status()

        weather_data = weather_response.json()

        # ====================================================
        # GET CURRENT DATA
        # ====================================================

        current = weather_data.get(
            "current",
            {}
        )

        if not current:

            return {
                "success": False,
                "message": (
                    "The weather service returned "
                    "no current weather data."
                )
            }

        # ====================================================
        # EXTRACT WEATHER VALUES
        # ====================================================

        temperature = current.get(
            "temperature_2m"
        )

        humidity = current.get(
            "relative_humidity_2m"
        )

        feels_like = current.get(
            "apparent_temperature"
        )

        precipitation = current.get(
            "precipitation"
        )

        wind_speed = current.get(
            "wind_speed_10m"
        )

        weather_code = current.get(
            "weather_code"
        )

        # ====================================================
        # CONVERT WEATHER CODE TO DESCRIPTION
        # ====================================================

        description = weather_description(
            weather_code
        )

        # ====================================================
        # RETURN RESULT
        # ====================================================

        return {
            "success": True,

            "city": location_name,

            "country": country,

            "temperature": temperature,

            "humidity": humidity,

            "feels_like": feels_like,

            "precipitation": precipitation,

            "wind_speed": wind_speed,

            "description": description
        }

    # ========================================================
    # REQUEST / INTERNET ERROR
    # ========================================================

    except requests.exceptions.RequestException as e:

        print()
        print("========================================")
        print("WEATHER API REQUEST ERROR")
        print("========================================")
        print("Error:", repr(e))
        print("========================================")
        print()

        return {
            "success": False,
            "message": (
                "I couldn't reach the weather service."
            )
        }

    # ========================================================
    # JSON ERROR
    # ========================================================

    except ValueError as e:

        print()
        print("========================================")
        print("WEATHER API JSON ERROR")
        print("========================================")
        print("Error:", repr(e))
        print("========================================")
        print()

        return {
            "success": False,
            "message": (
                "The weather service returned "
                "an invalid response."
            )
        }

    # ========================================================
    # GENERAL ERROR
    # ========================================================

    except Exception as e:

        print()
        print("========================================")
        print("WEATHER ERROR")
        print("========================================")
        print("Error:", repr(e))
        print("========================================")
        print()

        return {
            "success": False,
            "message": (
                "Something went wrong while "
                "getting the weather."
            )
        }


# ============================================================
# WEATHER CODE DESCRIPTION
# ============================================================

def weather_description(code):

    descriptions = {

        0: "clear sky",

        1: "mainly clear",

        2: "partly cloudy",

        3: "overcast",

        45: "fog",

        48: "depositing rime fog",

        51: "light drizzle",

        53: "moderate drizzle",

        55: "dense drizzle",

        56: "light freezing drizzle",

        57: "dense freezing drizzle",

        61: "slight rain",

        63: "moderate rain",

        65: "heavy rain",

        66: "light freezing rain",

        67: "heavy freezing rain",

        71: "slight snow",

        73: "moderate snow",

        75: "heavy snow",

        77: "snow grains",

        80: "slight rain showers",

        81: "moderate rain showers",

        82: "violent rain showers",

        85: "slight snow showers",

        86: "heavy snow showers",

        95: "thunderstorm",

        96: "thunderstorm with slight hail",

        99: "thunderstorm with heavy hail"
    }

    return descriptions.get(
        code,
        "unknown conditions"
    )
