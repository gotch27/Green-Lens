from django.http import JsonResponse
import requests
from django.conf import settings


def health_check(request):
    return JsonResponse({"status": "ok", "message": "Server is active"})

def get_weather(request):
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')

    if not lat or not lon:
        return JsonResponse({'error': 'Missing coordinates (lat, lon)'}, status=400)

    API_KEY = settings.OPENWEATHERMAP_API_KEY

    if not API_KEY:
        return JsonResponse({'error': 'API key not configured'}, status=500)

    # OpenWeather URL
    url = f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric'

    try:
        response = requests.get(url)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    if response.status_code != 200:
        return JsonResponse({'error': 'External API failed'}, status=500)

    data = response.json()

    return JsonResponse({
        'temperature': data['main']['temp'],
        'humidity': data['main']['humidity']
    })
