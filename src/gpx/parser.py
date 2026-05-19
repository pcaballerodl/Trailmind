import gpxpy
import gpxpy.gpx


def parsear_gpx(archivo):
    """
    Recibe un file-like object con contenido GPX.
    Devuelve un diccionario con todos los datos del track
    listos para ser analizados por la IA.
    """
    from .calculadora import (
        calcular_distancia_total,
        calcular_desnivel,
        calcular_estadisticas_altitud,
    )

    nombre_archivo = getattr(archivo, "filename", "")
    if not nombre_archivo.lower().endswith(".gpx"):
        raise ValueError("El archivo debe tener extensión .gpx")

    try:
        gpx = gpxpy.parse(archivo)
    except Exception:
        raise ValueError("El archivo no es un GPX válido")

    puntos = _extraer_puntos(gpx)

    if not puntos:
        raise ValueError("El GPX no contiene puntos de track")

    tiene_timestamps = puntos[0]["timestamp"] is not None

    desnivel = calcular_desnivel(puntos)
    altitud = calcular_estadisticas_altitud(puntos)

    return {
        "nombre_track": _nombre_track(gpx),
        "total_puntos": len(puntos),
        "distancia_km": calcular_distancia_total(puntos),
        "desnivel_positivo_m": desnivel["positivo"],
        "desnivel_negativo_m": desnivel["negativo"],
        "altitud_max_m": altitud["max"],
        "altitud_min_m": altitud["min"],
        "altitud_media_m": altitud["media"],
        "tiene_timestamps": tiene_timestamps,
        "puntos": puntos,
    }


def _extraer_puntos(gpx):
    """Concatena todos los segmentos de todos los tracks en una lista plana."""
    puntos = []
    for track in gpx.tracks:
        for segmento in track.segments:
            for punto in segmento.points:
                puntos.append({
                    "lat": punto.latitude,
                    "lon": punto.longitude,
                    "elevacion_m": punto.elevation,
                    "timestamp": punto.time.isoformat() if punto.time else None,
                })
    return puntos


def _nombre_track(gpx):
    """Nombre del primer track, o cadena vacía si no tiene."""
    if gpx.tracks and gpx.tracks[0].name:
        return gpx.tracks[0].name
    return ""
