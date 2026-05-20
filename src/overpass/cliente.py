import requests

_URL_OVERPASS = "https://overpass-api.de/api/interpreter"
_TIMEOUT_SEGUNDOS = 35


def consultar_overpass(query_ql):
    """
    Envía la consulta Overpass QL y devuelve el JSON crudo.
    Lanza RuntimeError si la petición falla.
    """
    try:
        respuesta = requests.post(
            _URL_OVERPASS,
            data={"data": query_ql},
            timeout=_TIMEOUT_SEGUNDOS,
            headers={"User-Agent": "TrailMind/1.0"},
        )
        respuesta.raise_for_status()
    except requests.exceptions.Timeout:
        raise RuntimeError("Overpass API no respondió a tiempo (timeout 35s)")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Error de red al consultar Overpass: {e}")

    return respuesta.json()
