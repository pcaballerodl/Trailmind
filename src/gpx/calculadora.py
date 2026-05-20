import gpxpy.geo


def calcular_tramos_duros(puntos):
    """Porcentaje de distancia con pendiente superior al 25%."""
    dist_total = 0.0
    dist_dura = 0.0

    for i in range(1, len(puntos)):
        p1, p2 = puntos[i - 1], puntos[i]
        if p1["elevacion_m"] is None or p2["elevacion_m"] is None:
            continue
        dist_h = gpxpy.geo.haversine_distance(p1["lat"], p1["lon"], p2["lat"], p2["lon"])
        if dist_h < 0.1:
            continue
        pendiente = abs(p2["elevacion_m"] - p1["elevacion_m"]) / dist_h * 100
        dist_total += dist_h
        if pendiente > 25:
            dist_dura += dist_h

    if dist_total == 0:
        return None
    return round(dist_dura / dist_total * 100, 1)


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
