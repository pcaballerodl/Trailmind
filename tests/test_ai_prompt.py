import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ai.prompt import construir_sistema, construir_usuario

TRACK_COMPLETO = {
    "nombre_track": "Ruta al Aneto",
    "distancia_km": 18.5,
    "desnivel_positivo_m": 1450.0,
    "desnivel_negativo_m": 1450.0,
    "altitud_max_m": 3404.0,
    "altitud_min_m": 1950.0,
    "altitud_media_m": 2700.0,
    "total_puntos": 3200,
    "tiene_timestamps": False,
}

TRACK_SIN_ALTITUD = {
    "nombre_track": "",
    "distancia_km": 5.0,
    "desnivel_positivo_m": 0.0,
    "desnivel_negativo_m": 0.0,
    "altitud_max_m": None,
    "altitud_min_m": None,
    "altitud_media_m": None,
    "total_puntos": 100,
    "tiene_timestamps": True,
}

PREVISION = {
    "fecha_inicio": "2024-07-15",
    "num_dias": 2,
    "dias": [
        {
            "fecha": "2024-07-15",
            "descripcion": "Despejado",
            "temp_max_c": 22.0,
            "temp_min_c": 8.0,
            "precipitacion_mm": 0.0,
            "nieve_cm": 0.0,
            "viento_max_kmh": 15.0,
            "codigo_wmo": 0,
        },
        {
            "fecha": "2024-07-16",
            "descripcion": "Tormenta",
            "temp_max_c": 12.0,
            "temp_min_c": 4.0,
            "precipitacion_mm": 18.0,
            "nieve_cm": 5.0,
            "viento_max_kmh": 65.0,
            "codigo_wmo": 95,
        },
    ],
}

PREFERENCIAS = {"dias": 2, "nivel": "avanzado", "personas": 3}


class TestConstruirSistema:
    def test_devuelve_string_no_vacio(self):
        resultado = construir_sistema()
        assert isinstance(resultado, str)
        assert len(resultado) > 50

    def test_menciona_montana(self):
        resultado = construir_sistema().lower()
        assert "montaña" in resultado

    def test_menciona_markdown(self):
        resultado = construir_sistema().lower()
        assert "markdown" in resultado

    def test_menciona_espanol(self):
        resultado = construir_sistema().lower()
        assert "español" in resultado


class TestConstruirUsuario:
    def test_incluye_distancia(self):
        prompt = construir_usuario(TRACK_COMPLETO, None, PREFERENCIAS)
        assert "18.5" in prompt

    def test_incluye_desnivel(self):
        prompt = construir_usuario(TRACK_COMPLETO, None, PREFERENCIAS)
        assert "1450" in prompt

    def test_incluye_altitud_maxima(self):
        prompt = construir_usuario(TRACK_COMPLETO, None, PREFERENCIAS)
        assert "3404" in prompt

    def test_incluye_nombre_track(self):
        prompt = construir_usuario(TRACK_COMPLETO, None, PREFERENCIAS)
        assert "Aneto" in prompt

    def test_sin_nombre_usa_sin_nombre(self):
        prompt = construir_usuario(TRACK_SIN_ALTITUD, None, PREFERENCIAS)
        assert "Sin nombre" in prompt

    def test_incluye_nivel_grupo(self):
        prompt = construir_usuario(TRACK_COMPLETO, None, PREFERENCIAS)
        assert "avanzado" in prompt

    def test_incluye_numero_dias(self):
        prompt = construir_usuario(TRACK_COMPLETO, None, PREFERENCIAS)
        assert "2" in prompt

    def test_incluye_personas(self):
        prompt = construir_usuario(TRACK_COMPLETO, None, PREFERENCIAS)
        assert "3" in prompt

    def test_sin_prevision_indica_no_disponible(self):
        prompt = construir_usuario(TRACK_COMPLETO, None, PREFERENCIAS)
        assert "no" in prompt.lower() and ("previsión" in prompt.lower() or "meteorológica" in prompt.lower())

    def test_con_prevision_incluye_temperatura(self):
        prompt = construir_usuario(TRACK_COMPLETO, PREVISION, PREFERENCIAS)
        assert "22.0" in prompt or "22" in prompt

    def test_con_prevision_incluye_descripcion(self):
        prompt = construir_usuario(TRACK_COMPLETO, PREVISION, PREFERENCIAS)
        assert "Despejado" in prompt
        assert "Tormenta" in prompt

    def test_con_prevision_incluye_nieve(self):
        prompt = construir_usuario(TRACK_COMPLETO, PREVISION, PREFERENCIAS)
        assert "5.0" in prompt or "nieve" in prompt.lower()

    def test_sin_altitud_indica_no_disponible(self):
        prompt = construir_usuario(TRACK_SIN_ALTITUD, None, PREFERENCIAS)
        assert "no disponibles" in prompt.lower()

    def test_no_incluye_array_puntos(self):
        # El array puntos nunca debe aparecer en el prompt
        track_con_puntos = dict(TRACK_COMPLETO)
        track_con_puntos["puntos"] = [{"lat": 1, "lon": 2}] * 100
        prompt = construir_usuario(track_con_puntos, None, PREFERENCIAS)
        assert '"puntos"' not in prompt
        assert "lat" not in prompt

    def test_incluye_secciones_requeridas(self):
        prompt = construir_usuario(TRACK_COMPLETO, None, PREFERENCIAS)
        assert "Itinerario" in prompt
        assert "Equipamiento" in prompt
        assert "seguridad" in prompt.lower()
