def construir_sistema():
    return (
        "Eres TrailMind, un planificador experto de expediciones de montaña. "
        "Tu misión es generar planes de expedición detallados, seguros y prácticos en español.\n\n"
        "Normas:\n"
        "- Responde siempre en español.\n"
        "- Usa formato Markdown con secciones claras (##, ###, listas con -).\n"
        "- Basa el plan únicamente en los datos técnicos facilitados; no inventes características del terreno.\n"
        "- Si no hay previsión meteorológica, ofrece consejos generales de seguridad.\n"
        "- Adapta el ritmo y las recomendaciones al nivel del grupo indicado.\n"
        "- Incluye siempre advertencias de seguridad relevantes.\n"
        "- Sé concreto: usa cifras reales del track (distancia, desnivel, altitudes) en el itinerario."
    )


def construir_usuario(track, prevision, preferencias):
    lineas = []

    # Datos técnicos del track
    lineas.append("## Datos del track")
    lineas.append(f"- Nombre: {track.get('nombre_track') or 'Sin nombre'}")
    lineas.append(f"- Distancia total: {track['distancia_km']} km")
    lineas.append(f"- Desnivel positivo (D+): {track['desnivel_positivo_m']} m")
    lineas.append(f"- Desnivel negativo (D-): {track['desnivel_negativo_m']} m")

    if track.get("altitud_max_m") is not None:
        lineas.append(f"- Altitud máxima: {track['altitud_max_m']} m")
        lineas.append(f"- Altitud mínima: {track['altitud_min_m']} m")
        lineas.append(f"- Altitud media: {track['altitud_media_m']} m")
    else:
        lineas.append("- Datos de altitud: no disponibles")

    lineas.append(f"- Puntos GPS registrados: {track['total_puntos']}")
    lineas.append(f"- Con timestamps: {'Sí' if track.get('tiene_timestamps') else 'No'}")
    lineas.append("")

    # Preferencias de la expedición
    lineas.append("## Preferencias de la expedición")
    lineas.append(f"- Número de días: {preferencias['dias']}")
    lineas.append(f"- Nivel del grupo: {preferencias['nivel']}")
    lineas.append(f"- Número de personas: {preferencias.get('personas', 1)}")
    lineas.append("")

    # Previsión meteorológica
    lineas.append("## Previsión meteorológica")
    if prevision is None:
        lineas.append(
            "No se ha facilitado previsión meteorológica. "
            "Ofrece consejos generales de seguridad adaptados a montaña de media-alta montaña."
        )
    else:
        lineas.append(f"Fecha de inicio: {prevision['fecha_inicio']} — {prevision['num_dias']} días cubiertos")
        lineas.append("")
        for dia in prevision["dias"]:
            partes = [f"**{dia['fecha']}**: {dia['descripcion']}"]
            if dia.get("temp_max_c") is not None:
                partes.append(f"máx {dia['temp_max_c']}°C / mín {dia['temp_min_c']}°C")
            if dia.get("precipitacion_mm") and dia["precipitacion_mm"] > 0:
                partes.append(f"precipitación {dia['precipitacion_mm']} mm")
            if dia.get("nieve_cm") and dia["nieve_cm"] > 0:
                partes.append(f"nieve {dia['nieve_cm']} cm")
            if dia.get("viento_max_kmh") is not None:
                partes.append(f"viento máx {dia['viento_max_kmh']} km/h")
            lineas.append("- " + ", ".join(partes))
    lineas.append("")

    # Instrucción de salida
    lineas.append("## Genera el plan de expedición con exactamente estas secciones:")
    lineas.append("1. **Resumen del recorrido y valoración de dificultad**")
    lineas.append("2. **Itinerario detallado por etapas** (con horarios orientativos y puntos de referencia)")
    lineas.append("3. **Puntos clave y precauciones en ruta**")
    lineas.append("4. **Equipamiento recomendado** para las condiciones específicas")
    lineas.append("5. **Alimentación e hidratación** (cantidades orientativas por persona y día)")
    lineas.append("6. **Análisis meteorológico y recomendaciones de seguridad**")

    return "\n".join(lineas)
