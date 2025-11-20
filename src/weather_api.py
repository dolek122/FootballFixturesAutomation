import requests
from robot.api.deco import keyword

@keyword
def get_weather(latitude, longitude):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()
        temp_c = data['current_weather']['temperature']

        temp_f = round((temp_c * 1.8) + 32, 2)

        return {
            'celsius': temp_c,
            'fahrenheit': temp_f,
            'full_response': data
        }

    except requests.exceptions.RequestException as e:
        raise Exception(f"Błąd API: {e}")