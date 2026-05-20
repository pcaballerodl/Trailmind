_CODIGOS_WMO = {
    0:  "Despejado",
    1:  "Principalmente despejado",
    2:  "Parcialmente nublado",
    3:  "Nublado",
    45: "Niebla",
    48: "Niebla engelante",
    51: "Llovizna ligera",
    53: "Llovizna moderada",
    55: "Llovizna densa",
    56: "Llovizna engelante ligera",
    57: "Llovizna engelante densa",
    61: "Lluvia ligera",
    63: "Lluvia moderada",
    65: "Lluvia fuerte",
    66: "Lluvia helada ligera",
    67: "Lluvia helada fuerte",
    71: "Nevada ligera",
    73: "Nevada moderada",
    75: "Nevada fuerte",
    77: "Granizo",
    80: "Chubascos ligeros",
    81: "Chubascos moderados",
    82: "Chubascos fuertes",
    85: "Chubascos de nieve ligeros",
    86: "Chubascos de nieve fuertes",
    95: "Tormenta",
    96: "Tormenta con granizo ligero",
    99: "Tormenta con granizo fuerte",
}


def codigo_wmo_a_descripcion(codigo):
    return _CODIGOS_WMO.get(codigo, f"Código {codigo}")


def procesar_respuesta(respuesta_json, lat, lon, fecha_inicio):
    """
    Transforma la respuesta cruda de Open-Meteo en el dict limpio
    que consumirá la IA y el frontend.
    """
    if "error" in respuesta_json:
        raise RuntimeError(respuesta_json.get("reason", "Error de Open-Meteo"))

    diario = respuesta_json.get("daily", {})
    fechas = diario.get("time", [])
    temp_max = diario.get("temperature_2m_max", [])
    temp_min = diario.get("temperature_2m_min", [])
    precipitacion = diario.get("precipitation_sum", [])
    nieve = diario.get("snowfall_sum", [])
    viento = diario.get("wind_speed_10m_max", [])
    codigos = diario.get("weather_code", [])

    dias = []
    for i, fecha in enumerate(fechas):
        dias.append({
            "fecha": fecha,
            "descripcion": codigo_wmo_a_descripcion(
                int(codigos[i]) if i < len(codigos) and codigos[i] is not None else 0
            ),
            "temp_max_c": _redondear(temp_max, i),
            "temp_min_c": _redondear(temp_min, i),
            "precipitacion_mm": _redondear(precipitacion, i),
            "nieve_cm": _redondear(nieve, i),
            "viento_max_kmh": _redondear(viento, i),
            "codigo_wmo": int(codigos[i]) if i < len(codigos) and codigos[i] is not None else 0,
        })

    return {
        "ubicacion": {"lat": lat, "lon": lon},
        "fecha_inicio": fecha_inicio,
        "num_dias": len(dias),
        "dias": dias,
    }


def _redondear(lista, indice):
    if indice < len(lista) and lista[indice] is not None:
        return round(float(lista[indice]), 1)
    return None
