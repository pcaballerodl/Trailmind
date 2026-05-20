import sys
import os
import pytest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

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


class TestCodigosWmoMontana:
    """Códigos especialmente relevantes para montaña que deben tener descripción."""

    def test_llovizna_engelante(self):
        assert "engelante" in codigo_wmo_a_descripcion(56).lower()
        assert "engelante" in codigo_wmo_a_descripcion(57).lower()

    def test_lluvia_helada(self):
        assert "helada" in codigo_wmo_a_descripcion(66).lower()
        assert "helada" in codigo_wmo_a_descripcion(67).lower()

    def test_todos_los_codigos_wmo_conocidos(self):
        codigos_esperados = [0, 1, 2, 3, 45, 48, 51, 53, 55, 56, 57,
                             61, 63, 65, 66, 67, 71, 73, 75, 77,
                             80, 81, 82, 85, 86, 95, 96, 99]
        for codigo in codigos_esperados:
            desc = codigo_wmo_a_descripcion(codigo)
            assert not desc.startswith("Código"), f"Código {codigo} no tiene descripción"


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

    def test_respuesta_sin_daily_no_rompe(self):
        resultado = procesar_respuesta({}, 42.0, 0.0, "2024-07-15")
        assert resultado["num_dias"] == 0
        assert resultado["dias"] == []


class TestClienteOpenMeteo:
    """Tests del cliente HTTP con llamadas mockeadas."""

    def test_timeout_lanza_runtime_error(self):
        import requests
        with patch("weather.cliente.requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout()
            from weather.cliente import consultar_open_meteo
            with pytest.raises(RuntimeError, match="tiempo"):
                consultar_open_meteo(42.0, 0.0, "2024-07-15", 3)

    def test_error_de_red_lanza_runtime_error(self):
        import requests
        with patch("weather.cliente.requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError("sin conexión")
            from weather.cliente import consultar_open_meteo
            with pytest.raises(RuntimeError, match="Error de red"):
                consultar_open_meteo(42.0, 0.0, "2024-07-15", 3)

    def test_respuesta_200_con_error_json_lanza_runtime_error(self):
        respuesta_mock = MagicMock()
        respuesta_mock.raise_for_status.return_value = None
        respuesta_mock.json.return_value = {
            "error": True,
            "reason": "Invalid coordinates"
        }
        with patch("weather.cliente.requests.get", return_value=respuesta_mock):
            from weather.cliente import consultar_open_meteo
            with pytest.raises(RuntimeError, match="Invalid coordinates"):
                consultar_open_meteo(999.0, 0.0, "2024-07-15", 3)

    def test_calcula_fecha_fin_correctamente(self):
        respuesta_mock = MagicMock()
        respuesta_mock.raise_for_status.return_value = None
        respuesta_mock.json.return_value = {"daily": {"time": []}}
        with patch("weather.cliente.requests.get", return_value=respuesta_mock) as mock_get:
            from weather.cliente import consultar_open_meteo
            consultar_open_meteo(42.0, 0.0, "2024-07-15", 5)
            params = mock_get.call_args[1]["params"]
            assert params["start_date"] == "2024-07-15"
            assert params["end_date"] == "2024-07-19"


class TestEndpointMeteo:
    """Tests del endpoint Flask con obtener_prevision mockeado."""

    @pytest.fixture
    def cliente_flask(self):
        import main
        main.app.config["TESTING"] = True
        return main.app.test_client()

    def test_lat_lon_ausentes_devuelve_400(self, cliente_flask):
        r = cliente_flask.get("/api/meteo/prevision?fecha=2099-01-01")
        assert r.status_code == 400
        datos = r.get_json()
        assert datos["ok"] is False

    def test_fecha_pasada_devuelve_400(self, cliente_flask):
        r = cliente_flask.get("/api/meteo/prevision?lat=42&lon=0&fecha=2000-01-01")
        assert r.status_code == 400
        assert "próximos 16" in r.get_json()["error"]

    def test_fecha_demasiado_lejana_devuelve_400(self, cliente_flask):
        fecha_lejana = (date.today() + timedelta(days=20)).isoformat()
        r = cliente_flask.get(f"/api/meteo/prevision?lat=42&lon=0&fecha={fecha_lejana}")
        assert r.status_code == 400

    def test_rango_excede_16_dias_devuelve_400(self, cliente_flask):
        # fecha=hoy+12, dias=7 → fin=hoy+18 > 16 días
        fecha = (date.today() + timedelta(days=12)).isoformat()
        r = cliente_flask.get(f"/api/meteo/prevision?lat=42&lon=0&fecha={fecha}&dias=7")
        assert r.status_code == 400
        assert "excede" in r.get_json()["error"]

    def test_dias_fuera_de_rango_devuelve_400(self, cliente_flask):
        fecha = date.today().isoformat()
        r = cliente_flask.get(f"/api/meteo/prevision?lat=42&lon=0&fecha={fecha}&dias=20")
        assert r.status_code == 400

    def test_coordenadas_invalidas_devuelve_400(self, cliente_flask):
        fecha = date.today().isoformat()
        r = cliente_flask.get(f"/api/meteo/prevision?lat=999&lon=0&fecha={fecha}")
        assert r.status_code == 400
        assert "rango" in r.get_json()["error"]

    def test_prevision_correcta_devuelve_200(self, cliente_flask):
        prevision_mock = {
            "ubicacion": {"lat": 42.0, "lon": 0.0},
            "fecha_inicio": date.today().isoformat(),
            "num_dias": 1,
            "dias": [],
        }
        fecha = date.today().isoformat()
        with patch("main.obtener_prevision", return_value=prevision_mock):
            r = cliente_flask.get(f"/api/meteo/prevision?lat=42&lon=0&fecha={fecha}&dias=1")
        assert r.status_code == 200
        datos = r.get_json()
        assert datos["ok"] is True
        assert "prevision" in datos

    def test_error_open_meteo_devuelve_502(self, cliente_flask):
        fecha = date.today().isoformat()
        with patch("main.obtener_prevision", side_effect=RuntimeError("API caída")):
            r = cliente_flask.get(f"/api/meteo/prevision?lat=42&lon=0&fecha={fecha}&dias=1")
        assert r.status_code == 502
        assert r.get_json()["ok"] is False
