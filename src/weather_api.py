import requests
from robot.api.deco import keyword

@keyword
def get_weather(latitude, longitude):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true"
    response = requests.get(url)
    data = response.json()
    temperature_c = data['current_weather']['temperature']
    temperature_f = round((temperature_c * 9/5) + 32, 2)
    return {
        'celsius': temperature_c,
        'fahrenheit': temperature_f,
        'full_response': data
    }
