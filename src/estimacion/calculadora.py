import math
from datetime import date


def estimar_tiempo(track, mes=None):
    """
    Calcula la estimación de tiempo para un track usando Naismith modificado.
    Aplica factores de altitud, pendiente dura y condiciones de nieve.
    Devuelve estimaciones óptima y desfavorable.
    """
    distancia_km = float(track.get("distancia_km") or 0)
    desnivel_pos = float(track.get("desnivel_positivo_m") or 0)
    desnivel_neg = float(track.get("desnivel_negativo_m") or 0)
    altitud_media = float(track.get("altitud_media_m") or 0)
    altitud_max = float(track.get("altitud_max_m") or 0)
    tramos_duros_pct = track.get("tramos_duros_pct")

    if mes is None:
        mes = date.today().month

    # ── Fórmula de Naismith (base) ──────────────────────────────────────────
    # 5 km/h en llano + 1h por cada 600m de subida + 0.4h por cada 300m de bajada
    horas_base = max(0.1, (distancia_km / 5.0) + (desnivel_pos / 600) + (desnivel_neg / 300 * 0.4))

    # ── Factor altitud (penalización por oxígeno reducido) ──────────────────
    if altitud_media > 3500:
        factor_alt = 1.35
    elif altitud_media > 3000:
        factor_alt = 1.22
    elif altitud_media > 2500:
        factor_alt = 1.12
    else:
        factor_alt = 1.0

    # ── Penalización por tramos de pendiente extrema (>25%) ─────────────────
    if tramos_duros_pct is not None and tramos_duros_pct > 0:
        penalizacion_pendiente = horas_base * tramos_duros_pct * 0.005
    else:
        penalizacion_pendiente = 0.0

    # ── Factor nieve / condiciones invernales ────────────────────────────────
    meses_nieve = {11, 12, 1, 2, 3}
    factor_nieve = 1.0
    if mes in meses_nieve:
        if altitud_max > 3000:
            factor_nieve = 1.30
        elif altitud_max > 2000:
            factor_nieve = 1.15
        elif altitud_max > 1500:
            factor_nieve = 1.07

    # ── Estimaciones finales ─────────────────────────────────────────────────
    horas_optimo = (horas_base + penalizacion_pendiente) * factor_alt
    horas_desfavorable = horas_optimo * factor_nieve * 1.15

    return {
        "optimo": _formatear_tiempo(horas_optimo),
        "desfavorable": _formatear_tiempo(horas_desfavorable),
        "factores": {
            "factor_altitud": factor_alt,
            "factor_nieve": factor_nieve,
            "con_datos_pendiente": tramos_duros_pct is not None and tramos_duros_pct > 0,
        },
    }


def estimar_tiempo_tramos(puntos, mes=None):
    """
    Calcula el tiempo acumulado punto a punto aplicando Naismith por segmento.
    Devuelve una lista de N dicts (uno por punto) con km_acum y tiempos acumulados.
    """
    if mes is None:
        mes = date.today().month

    altitudes = [p.get("elevacion_m") for p in puntos]
    altitud_max = max((a for a in altitudes if a is not None), default=0)

    meses_nieve = {11, 12, 1, 2, 3}
    factor_nieve = 1.0
    if mes in meses_nieve:
        if altitud_max > 3000:
            factor_nieve = 1.30
        elif altitud_max > 2000:
            factor_nieve = 1.15
        elif altitud_max > 1500:
            factor_nieve = 1.07

    resultado = []
    km_acum = 0.0
    min_opt_acum = 0.0
    min_des_acum = 0.0

    for i, p in enumerate(puntos):
        if i == 0:
            resultado.append({
                "indice": 0,
                "km_acum": 0.0,
                "alt_m": p.get("elevacion_m"),
                "lat": p.get("lat"),
                "lon": p.get("lon"),
                "tiempo_optimo_min": 0.0,
                "tiempo_desfavorable_min": 0.0,
            })
            continue

        p_prev = puntos[i - 1]
        dist_km = _haversine_km(p_prev, p)
        km_acum += dist_km

        alt_prev = p_prev.get("elevacion_m")
        alt_curr = p.get("elevacion_m")

        if alt_prev is not None and alt_curr is not None:
            diff = alt_curr - alt_prev
            desnivel_pos = max(0.0, diff)
            desnivel_neg = max(0.0, -diff)
            altitud_local = alt_prev
        else:
            desnivel_pos = 0.0
            desnivel_neg = 0.0
            altitud_local = 0.0

        factor_alt = _factor_altitud(altitud_local)

        horas_base = (dist_km / 5.0) + (desnivel_pos / 600) + (desnivel_neg / 300 * 0.4)
        horas_opt_seg = horas_base * factor_alt
        horas_des_seg = horas_opt_seg * factor_nieve * 1.15

        min_opt_acum += horas_opt_seg * 60
        min_des_acum += horas_des_seg * 60

        resultado.append({
            "indice": i,
            "km_acum": round(km_acum, 4),
            "alt_m": alt_curr,
            "lat": p.get("lat"),
            "lon": p.get("lon"),
            "tiempo_optimo_min": round(min_opt_acum, 2),
            "tiempo_desfavorable_min": round(min_des_acum, 2),
        })

    return resultado


def _factor_altitud(altitud_m):
    if altitud_m > 3500:
        return 1.35
    if altitud_m > 3000:
        return 1.22
    if altitud_m > 2500:
        return 1.12
    return 1.0


def _haversine_km(a, b):
    R = 6371.0
    lat1 = math.radians(a.get("lat", 0))
    lat2 = math.radians(b.get("lat", 0))
    dlat = lat2 - lat1
    dlon = math.radians(b.get("lon", 0) - a.get("lon", 0))
    x = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(x), math.sqrt(1 - x))


def _formatear_tiempo(horas_float):
    total_min = round(horas_float * 60)
    return {
        "horas": total_min // 60,
        "minutos": total_min % 60,
        "total_min": total_min,
    }
