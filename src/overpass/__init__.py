from .cliente import consultar_overpass
from .procesador import construir_query, expandir_bbox, procesar_elementos


def buscar_pois(bbox, radio_m, tipos=None):
    """
    Busca refugios y fuentes en el área del track ampliada por radio_m metros.
    Devuelve una lista de dicts con lat, lon, tipo y nombre.
    """
    if tipos is None:
        tipos = ["fuente", "refugio"]

    bbox_expandido = expandir_bbox(
        bbox["min_lat"], bbox["max_lat"],
        bbox["min_lon"], bbox["max_lon"],
        radio_m,
    )
    query = construir_query(bbox_expandido, tipos)
    respuesta = consultar_overpass(query)
    return procesar_elementos(respuesta, tipos)


__all__ = ["buscar_pois"]
