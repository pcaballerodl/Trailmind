import math


INTERVALO_COMIDA_MIN  = 270   # 4.5 horas entre paradas de comida
DURACION_COMIDA_MIN   = 45
DURACION_CAMPAMENTO_MIN = 480  # 8 horas de descanso nocturno
VENTANA_AJUSTE_PLANO  = 15    # índices a explorar en cada dirección
RADIO_POI_CERCANO_M   = 800   # metros


def sugerir_checkpoints(tramos, pois=None, dias=1, modo="optimo"):
    """Sugiere checkpoints automáticos (comidas y campamentos) para un itinerario.

    Args:
        tramos: lista de puntos con km_acum, alt_m, lat, lon, tiempo_optimo_min, tiempo_desfavorable_min
        pois:   lista de POIs con tipo, lat, lon, nombre
        dias:   número de días del track
        modo:   "optimo" o "desfavorable"

    Returns:
        Lista de checkpoints ordenados por índice.
    """
    if pois is None:
        pois = []
    if not tramos or len(tramos) < 2:
        return []
    dias = max(1, int(dias))

    campo_tiempo = "tiempo_optimo_min" if modo == "optimo" else "tiempo_desfavorable_min"
    tiempo_total = tramos[-1].get(campo_tiempo, 0)
    if tiempo_total == 0:
        return []

    tiempo_por_dia = tiempo_total / dias
    checkpoints    = []
    indices_camps  = []

    # Campamentos: uno al final de cada día excepto el último
    for dia in range(1, dias):
        tiempo_obj = tiempo_por_dia * dia
        idx = _indice_en_tiempo(tramos, campo_tiempo, tiempo_obj)
        idx = _ajustar_zona_plana(tramos, idx)
        poi = _poi_mas_cercano(tramos[idx], pois, {"refugio"})
        checkpoints.append(_crear(
            tipo="campamento",
            indice=idx,
            tramos=tramos,
            etiqueta=f"Campamento día {dia}",
            duracion_min=DURACION_CAMPAMENTO_MIN,
            poi_cercano=poi,
        ))
        indices_camps.append(idx)

    # Segmentos de marcha: [0..camp1], [camp1..camp2], ..., [campN..fin]
    puntos_seg = [0] + indices_camps + [len(tramos) - 1]

    for k in range(len(puntos_seg) - 1):
        idx_ini = puntos_seg[k]
        idx_fin = puntos_seg[k + 1]
        t_ini   = tramos[idx_ini].get(campo_tiempo, 0)
        t_fin   = tramos[idx_fin].get(campo_tiempo, 0)
        duracion_seg = t_fin - t_ini

        # Segmentos cortos (< 3.4 horas): sin parada de comida
        if duracion_seg < INTERVALO_COMIDA_MIN * 0.75:
            continue

        t_comida = t_ini + INTERVALO_COMIDA_MIN
        while t_comida < t_fin - 60:
            idx = _indice_en_tiempo(tramos, campo_tiempo, t_comida)
            idx = max(idx_ini + 1, min(idx, idx_fin - 1))
            idx = _ajustar_zona_plana(tramos, idx)
            # Re-clamp tras ajuste de zona plana para no salirse del segmento
            idx = max(idx_ini + 1, min(idx, idx_fin - 1))

            if not _demasiado_cerca(idx, indices_camps, tramos, min_km=1.5):
                poi = _poi_mas_cercano(tramos[idx], pois, {"fuente", "refugio"})
                checkpoints.append(_crear(
                    tipo="comida",
                    indice=idx,
                    tramos=tramos,
                    etiqueta="Parada comida",
                    duracion_min=DURACION_COMIDA_MIN,
                    poi_cercano=poi,
                ))
            t_comida += INTERVALO_COMIDA_MIN

    return _deduplicar_y_ordenar(checkpoints)


# ── Helpers privados ──────────────────────────────────────────────────────────

def _indice_en_tiempo(tramos, campo_tiempo, tiempo_objetivo):
    """Índice cuyo tiempo acumulado se aproxima más a tiempo_objetivo."""
    mejor_idx  = 0
    mejor_diff = abs(tramos[0].get(campo_tiempo, 0) - tiempo_objetivo)
    for i, t in enumerate(tramos):
        diff = abs(t.get(campo_tiempo, 0) - tiempo_objetivo)
        if diff < mejor_diff:
            mejor_diff = diff
            mejor_idx  = i
    return mejor_idx


def _ajustar_zona_plana(tramos, idx):
    """Desplaza idx hacia la zona más plana dentro de ±VENTANA_AJUSTE_PLANO."""
    n     = len(tramos)
    inicio = max(0, idx - VENTANA_AJUSTE_PLANO)
    fin    = min(n - 1, idx + VENTANA_AJUSTE_PLANO)

    mejor_idx       = idx
    mejor_pendiente = _pendiente_media(tramos, idx)

    for i in range(inicio, fin + 1):
        p = _pendiente_media(tramos, i)
        if p < mejor_pendiente:
            mejor_pendiente = p
            mejor_idx       = i
    return mejor_idx


def _pendiente_media(tramos, idx):
    """Pendiente absoluta media (m/m) en el entorno del índice."""
    n       = len(tramos)
    vecinos = [i for i in (idx - 1, idx, idx + 1) if 0 <= i < n - 1]
    if not vecinos:
        return 0.0
    total = 0.0
    for i in vecinos:
        alt_a = tramos[i].get("alt_m") or 0
        alt_b = tramos[i + 1].get("alt_m") or 0
        km_a  = tramos[i].get("km_acum", 0)
        km_b  = tramos[i + 1].get("km_acum", 0)
        dist_m = max((km_b - km_a) * 1000, 1)
        total += abs(alt_b - alt_a) / dist_m
    return total / len(vecinos)


def _poi_mas_cercano(tramo, pois, tipos_buscados):
    """POI más cercano dentro de RADIO_POI_CERCANO_M o None."""
    lat = tramo.get("lat")
    lon = tramo.get("lon")
    if lat is None or lon is None or not pois:
        return None

    mejor      = None
    mejor_dist = RADIO_POI_CERCANO_M

    for poi in pois:
        if poi.get("tipo") not in tipos_buscados:
            continue
        plat = poi.get("lat")
        plon = poi.get("lon")
        if plat is None or plon is None:
            continue
        dist = _haversine_m(lat, lon, plat, plon)
        if dist < mejor_dist:
            mejor_dist = dist
            mejor = {
                "tipo":        poi.get("tipo"),
                "nombre":      poi.get("nombre"),
                "distancia_m": round(dist),
            }
    return mejor


def _haversine_m(lat1, lon1, lat2, lon2):
    R    = 6_371_000.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a    = (math.sin(dlat / 2) ** 2 +
            math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
            math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _demasiado_cerca(idx, indices_ref, tramos, min_km=1.5):
    """True si idx está a menos de min_km de algún índice de referencia."""
    km_idx = tramos[idx].get("km_acum", 0)
    for ref in indices_ref:
        if abs(km_idx - tramos[ref].get("km_acum", 0)) < min_km:
            return True
    return False


def _crear(tipo, indice, tramos, etiqueta, duracion_min, poi_cercano=None):
    t = tramos[indice]
    return {
        "id":          f"{tipo}_{indice}",
        "tipo":        tipo,
        "indice":      indice,
        "km_acum":     t.get("km_acum", 0),
        "alt_m":       t.get("alt_m"),
        "lat":         t.get("lat"),
        "lon":         t.get("lon"),
        "etiqueta":    etiqueta,
        "duracion_min": duracion_min,
        "auto":        True,
        "poi_cercano": poi_cercano,
    }


def _deduplicar_y_ordenar(checkpoints):
    """Elimina duplicados por índice (campamento > comida) y ordena."""
    vistos = {}
    for cp in checkpoints:
        idx = cp["indice"]
        if idx not in vistos or cp["tipo"] == "campamento":
            vistos[idx] = cp
    return sorted(vistos.values(), key=lambda cp: cp["indice"])
