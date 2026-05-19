from .cliente import consultar_open_meteo
from .procesador import procesar_respuesta


def obtener_prevision(lat, lon, fecha_inicio, num_dias=7):
    """
    Punto de entrada del módulo de meteorología.
    Devuelve el dict de previsión limpio listo para la IA y el frontend.
    """
    datos_crudos = consultar_open_meteo(lat, lon, fecha_inicio, num_dias)
    return procesar_respuesta(datos_crudos, lat, lon, fecha_inicio)


__all__ = ["obtener_prevision"]
