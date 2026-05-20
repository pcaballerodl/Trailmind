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


def _formatear_tiempo(horas_float):
    total_min = round(horas_float * 60)
    return {
        "horas": total_min // 60,
        "minutos": total_min % 60,
        "total_min": total_min,
    }
