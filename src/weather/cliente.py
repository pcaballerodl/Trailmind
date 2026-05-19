import requests
from datetime import datetime, timedelta

_URL_OPEN_METEO = "https://api.open-meteo.com/v1/forecast"
_TIMEOUT_SEGUNDOS = 10

_VARIABLES_DIARIAS = ",".join([
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "snowfall_sum",
    "wind_speed_10m_max",
    "weather_code",
])


def consultar_open_meteo(lat, lon, fecha_inicio, num_dias):
    """
    Llama a la API de Open-Meteo y devuelve el JSON crudo.
    Lanza RuntimeError si la petición falla o la API devuelve error.
    """
    fecha_fin = (
        datetime.strptime(fecha_inicio, "%Y-%m-%d") + timedelta(days=num_dias - 1)
    ).strftime("%Y-%m-%d")

    parametros = {
        "latitude": lat,
        "longitude": lon,
        "daily": _VARIABLES_DIARIAS,
        "start_date": fecha_inicio,
        "end_date": fecha_fin,
        "timezone": "auto",
        "wind_speed_unit": "kmh",
    }

    try:
        respuesta = requests.get(_URL_OPEN_METEO, params=parametros, timeout=_TIMEOUT_SEGUNDOS)
        respuesta.raise_for_status()
    except requests.exceptions.Timeout:
        raise RuntimeError("Open-Meteo no respondió a tiempo")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Error de red al consultar Open-Meteo: {e}")

    datos = respuesta.json()

    if "error" in datos:
        raise RuntimeError(datos.get("reason", "Error desconocido de Open-Meteo"))

    return datos
