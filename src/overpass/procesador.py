_TAGS_FUENTE = [
    ("amenity", "drinking_water"),
    ("natural", "spring"),
    ("amenity", "water_point"),
]

_TAGS_REFUGIO = [
    ("tourism", "alpine_hut"),
    ("tourism", "wilderness_hut"),
    ("amenity", "shelter"),
]


def construir_query(bbox, tipos):
    """Genera la consulta Overpass QL para el bbox y tipos solicitados."""
    sur, norte = bbox["sur"], bbox["norte"]
    oeste, este = bbox["oeste"], bbox["este"]

    tags = []
    if "fuente" in tipos:
        tags.extend(_TAGS_FUENTE)
    if "refugio" in tipos:
        tags.extend(_TAGS_REFUGIO)

    lineas = ["[out:json][timeout:30];", "("]
    for clave, valor in tags:
        area = f"({sur},{oeste},{norte},{este})"
        lineas.append(f'  node["{clave}"="{valor}"]{area};')
        lineas.append(f'  way["{clave}"="{valor}"]{area};')
    lineas += [");", "out center;"]

    return "\n".join(lineas)


def expandir_bbox(min_lat, max_lat, min_lon, max_lon, radio_m):
    """Amplía el bounding box del track en todas las direcciones por radio_m metros."""
    delta = radio_m / 111_000
    return {
        "sur":   round(min_lat - delta, 6),
        "norte": round(max_lat + delta, 6),
        "oeste": round(min_lon - delta, 6),
        "este":  round(max_lon + delta, 6),
    }


def procesar_elementos(respuesta_json, tipos):
    """Transforma la respuesta cruda de Overpass en una lista limpia de POIs."""
    pois = []
    for el in respuesta_json.get("elements", []):
        lat, lon = _coordenadas(el)
        if lat is None:
            continue
        tipo = _inferir_tipo(el.get("tags", {}), tipos)
        if tipo is None:
            continue
        tags = el.get("tags", {})
        pois.append({
            "lat":    lat,
            "lon":    lon,
            "tipo":   tipo,
            "nombre": tags.get("name") or tags.get("name:es") or None,
        })
    return pois


def _coordenadas(elemento):
    """Devuelve (lat, lon) para nodos y vías (usando el centroide)."""
    if elemento.get("type") == "node":
        return elemento.get("lat"), elemento.get("lon")
    if elemento.get("type") == "way":
        centro = elemento.get("center", {})
        return centro.get("lat"), centro.get("lon")
    return None, None


def _inferir_tipo(tags, tipos):
    if "fuente" in tipos:
        if (tags.get("amenity") in ("drinking_water", "water_point") or
                tags.get("natural") == "spring"):
            return "fuente"
    if "refugio" in tipos:
        if (tags.get("tourism") in ("alpine_hut", "wilderness_hut") or
                tags.get("amenity") == "shelter"):
            return "refugio"
    return None
