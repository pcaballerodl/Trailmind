import gpxpy.geo


def calcular_distancia_total(puntos):
    """Distancia total del track en kilómetros."""
    distancia_m = 0.0
    for i in range(1, len(puntos)):
        anterior = puntos[i - 1]
        actual = puntos[i]
        distancia_m += gpxpy.geo.haversine_distance(
            anterior["lat"], anterior["lon"],
            actual["lat"], actual["lon"]
        )
    return round(distancia_m / 1000, 3)


def calcular_desnivel(puntos):
    """Desnivel positivo y negativo acumulado en metros."""
    positivo = 0.0
    negativo = 0.0

    elevaciones = [p["elevacion_m"] for p in puntos if p["elevacion_m"] is not None]

    for i in range(1, len(elevaciones)):
        diferencia = elevaciones[i] - elevaciones[i - 1]
        if diferencia > 0:
            positivo += diferencia
        else:
            negativo += abs(diferencia)

    return {
        "positivo": round(positivo, 1),
        "negativo": round(negativo, 1),
    }


def calcular_estadisticas_altitud(puntos):
    """Altitud máxima, mínima y media en metros."""
    elevaciones = [p["elevacion_m"] for p in puntos if p["elevacion_m"] is not None]

    if not elevaciones:
        return {"max": None, "min": None, "media": None}

    return {
        "max": round(max(elevaciones), 1),
        "min": round(min(elevaciones), 1),
        "media": round(sum(elevaciones) / len(elevaciones), 1),
    }
