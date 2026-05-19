import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from weather.procesador import procesar_respuesta, codigo_wmo_a_descripcion

# Respuesta simulada con la estructura real de Open-Meteo
RESPUESTA_SIMULADA = {
    "latitude": 42.0,
    "longitude": 0.0,
    "timezone": "Europe/Madrid",
    "daily": {
        "time": ["2024-07-15", "2024-07-16", "2024-07-17"],
        "temperature_2m_max": [22.5, 18.0, 15.3],
        "temperature_2m_min": [8.1, 6.4, 5.0],
        "precipitation_sum": [0.0, 5.2, 12.8],
        "snowfall_sum": [0.0, 0.0, 3.5],
        "wind_speed_10m_max": [15.0, 28.0, 45.0],
        "weather_code": [2, 61, 73],
    },
}

RESPUESTA_CON_ERROR = {
    "error": True,
    "reason": "Parameter 'start_date' is out of allowed range",
}


class TestCodigoWmo:
    def test_codigo_conocido(self):
        assert codigo_wmo_a_descripcion(0) == "Despejado"
        assert codigo_wmo_a_descripcion(75) == "Nevada fuerte"
        assert codigo_wmo_a_descripcion(95) == "Tormenta"

    def test_codigo_desconocido(self):
        resultado = codigo_wmo_a_descripcion(999)
        assert "999" in resultado


class TestProcesarRespuesta:
    def setup_method(self):
        self.resultado = procesar_respuesta(RESPUESTA_SIMULADA, 42.0, 0.0, "2024-07-15")

    def test_estructura_raiz(self):
        assert "ubicacion" in self.resultado
        assert "fecha_inicio" in self.resultado
        assert "num_dias" in self.resultado
        assert "dias" in self.resultado

    def test_ubicacion(self):
        assert self.resultado["ubicacion"]["lat"] == 42.0
        assert self.resultado["ubicacion"]["lon"] == 0.0

    def test_fecha_inicio(self):
        assert self.resultado["fecha_inicio"] == "2024-07-15"

    def test_num_dias(self):
        assert self.resultado["num_dias"] == 3

    def test_estructura_dia(self):
        dia = self.resultado["dias"][0]
        claves = ["fecha", "descripcion", "temp_max_c", "temp_min_c",
                  "precipitacion_mm", "nieve_cm", "viento_max_kmh", "codigo_wmo"]
        for clave in claves:
            assert clave in dia, f"Falta la clave: {clave}"

    def test_descripcion_dia_despejado(self):
        assert self.resultado["dias"][0]["descripcion"] == "Parcialmente nublado"

    def test_temperatura_primer_dia(self):
        dia = self.resultado["dias"][0]
        assert dia["temp_max_c"] == pytest.approx(22.5, abs=0.1)
        assert dia["temp_min_c"] == pytest.approx(8.1, abs=0.1)

    def test_nieve_dia_con_nevada(self):
        dia = self.resultado["dias"][2]
        assert dia["nieve_cm"] == pytest.approx(3.5, abs=0.1)
        assert dia["descripcion"] == "Nevada moderada"

    def test_precipitacion_mm(self):
        dia = self.resultado["dias"][1]
        assert dia["precipitacion_mm"] == pytest.approx(5.2, abs=0.1)

    def test_viento_kmh(self):
        dia = self.resultado["dias"][2]
        assert dia["viento_max_kmh"] == pytest.approx(45.0, abs=0.1)


class TestErrores:
    def test_respuesta_con_error_lanza_excepcion(self):
        with pytest.raises(RuntimeError, match="out of allowed range"):
            procesar_respuesta(RESPUESTA_CON_ERROR, 42.0, 0.0, "2020-01-01")

    def test_valores_none_no_rompen(self):
        respuesta_con_nulos = {
            "daily": {
                "time": ["2024-07-15"],
                "temperature_2m_max": [None],
                "temperature_2m_min": [None],
                "precipitation_sum": [None],
                "snowfall_sum": [None],
                "wind_speed_10m_max": [None],
                "weather_code": [None],
            }
        }
        resultado = procesar_respuesta(respuesta_con_nulos, 42.0, 0.0, "2024-07-15")
        dia = resultado["dias"][0]
        assert dia["temp_max_c"] is None
        assert dia["nieve_cm"] is None
