import sys
import os
import json
import math
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from estimacion.calculadora import estimar_tiempo_tramos, _haversine_km, _factor_altitud

# ── Fixtures de puntos ────────────────────────────────────────────────────────

def _punto(lat, lon, elev):
    return {"lat": lat, "lon": lon, "elevacion_m": elev}

def _punto_sin_elev(lat, lon):
    return {"lat": lat, "lon": lon, "elevacion_m": None}

LLANO_2PTS = [
    _punto(42.0, 0.0, 1000),
    _punto(42.1, 0.0, 1000),  # ~11.1 km al norte, sin desnivel
]

SUBIDA_3PTS = [
    _punto(42.0, 0.0, 1000),
    _punto(42.05, 0.0, 1300),  # +300m
    _punto(42.10, 0.0, 1600),  # +300m
]

MIXTO_5PTS = [
    _punto(42.0, 0.0, 1000),
    _punto(42.02, 0.0, 1200),  # subida
    _punto(42.04, 0.0, 1200),  # llano
    _punto(42.06, 0.0, 1000),  # bajada
    _punto(42.08, 0.0, 1100),  # subida leve
]

ALTA_MONTANA = [
    _punto(45.0, 7.0, 3600),
    _punto(45.02, 7.0, 3800),
    _punto(45.04, 7.0, 4000),
]

PUNTOS_INVIERNO = [
    _punto(42.0, 0.0, 2100),
    _punto(42.05, 0.0, 2400),
    _punto(42.10, 0.0, 2600),
]


# ── Estructura del resultado ──────────────────────────────────────────────────

class TestEstructuraTramos:
    def test_devuelve_lista_misma_longitud(self):
        r = estimar_tiempo_tramos(LLANO_2PTS, mes=6)
        assert len(r) == 2

    def test_devuelve_lista_5_puntos(self):
        r = estimar_tiempo_tramos(MIXTO_5PTS, mes=6)
        assert len(r) == 5

    def test_claves_obligatorias(self):
        r = estimar_tiempo_tramos(LLANO_2PTS, mes=6)
        claves = {"indice", "km_acum", "alt_m", "lat", "lon",
                  "tiempo_optimo_min", "tiempo_desfavorable_min"}
        for punto in r:
            assert claves <= set(punto.keys())

    def test_primer_punto_tiempo_cero(self):
        r = estimar_tiempo_tramos(SUBIDA_3PTS, mes=6)
        assert r[0]["tiempo_optimo_min"] == 0.0
        assert r[0]["tiempo_desfavorable_min"] == 0.0

    def test_primer_punto_km_cero(self):
        r = estimar_tiempo_tramos(SUBIDA_3PTS, mes=6)
        assert r[0]["km_acum"] == 0.0

    def test_primer_punto_indice_cero(self):
        r = estimar_tiempo_tramos(SUBIDA_3PTS, mes=6)
        assert r[0]["indice"] == 0

    def test_indices_correlativo(self):
        r = estimar_tiempo_tramos(MIXTO_5PTS, mes=6)
        for i, pt in enumerate(r):
            assert pt["indice"] == i

    def test_lat_lon_preservados(self):
        r = estimar_tiempo_tramos(SUBIDA_3PTS, mes=6)
        for i, pt in enumerate(r):
            assert pt["lat"] == SUBIDA_3PTS[i]["lat"]
            assert pt["lon"] == SUBIDA_3PTS[i]["lon"]

    def test_alt_m_preservada(self):
        r = estimar_tiempo_tramos(SUBIDA_3PTS, mes=6)
        for i, pt in enumerate(r):
            assert pt["alt_m"] == SUBIDA_3PTS[i]["elevacion_m"]


# ── Monotonía y progresión ────────────────────────────────────────────────────

class TestMonotonia:
    def test_km_acum_crece_monotonicamente(self):
        r = estimar_tiempo_tramos(MIXTO_5PTS, mes=6)
        for i in range(1, len(r)):
            assert r[i]["km_acum"] > r[i - 1]["km_acum"]

    def test_tiempo_optimo_crece_monotonicamente(self):
        r = estimar_tiempo_tramos(MIXTO_5PTS, mes=6)
        for i in range(1, len(r)):
            assert r[i]["tiempo_optimo_min"] >= r[i - 1]["tiempo_optimo_min"]

    def test_tiempo_desfavorable_crece_monotonicamente(self):
        r = estimar_tiempo_tramos(MIXTO_5PTS, mes=6)
        for i in range(1, len(r)):
            assert r[i]["tiempo_desfavorable_min"] >= r[i - 1]["tiempo_desfavorable_min"]

    def test_desfavorable_siempre_mayor_que_optimo(self):
        r = estimar_tiempo_tramos(SUBIDA_3PTS, mes=6)
        for pt in r[1:]:  # punto 0 ambos son 0
            assert pt["tiempo_desfavorable_min"] > pt["tiempo_optimo_min"]

    def test_tiempo_total_positivo(self):
        r = estimar_tiempo_tramos(LLANO_2PTS, mes=6)
        assert r[-1]["tiempo_optimo_min"] > 0


# ── Lógica Naismith por segmento ─────────────────────────────────────────────

class TestLogicaNaismith:
    def test_subida_mas_lenta_que_llano(self):
        """Misma distancia: subida debe tardar más que llano."""
        llano = [_punto(42.0, 0.0, 1000), _punto(42.1, 0.0, 1000)]
        subida = [_punto(42.0, 0.0, 1000), _punto(42.1, 0.0, 1500)]
        r_llano  = estimar_tiempo_tramos(llano, mes=6)
        r_subida = estimar_tiempo_tramos(subida, mes=6)
        assert r_subida[-1]["tiempo_optimo_min"] > r_llano[-1]["tiempo_optimo_min"]

    def test_bajada_mas_lenta_que_llano(self):
        """Bajada también penaliza (0.4 factor en Naismith)."""
        llano  = [_punto(42.0, 0.0, 1000), _punto(42.1, 0.0, 1000)]
        bajada = [_punto(42.0, 0.0, 1500), _punto(42.1, 0.0, 1000)]
        r_llano  = estimar_tiempo_tramos(llano, mes=6)
        r_bajada = estimar_tiempo_tramos(bajada, mes=6)
        assert r_bajada[-1]["tiempo_optimo_min"] > r_llano[-1]["tiempo_optimo_min"]

    def test_mayor_distancia_mayor_tiempo(self):
        corto = [_punto(42.0, 0.0, 1000), _punto(42.05, 0.0, 1000)]
        largo = [_punto(42.0, 0.0, 1000), _punto(42.20, 0.0, 1000)]
        r_c = estimar_tiempo_tramos(corto, mes=6)
        r_l = estimar_tiempo_tramos(largo, mes=6)
        assert r_l[-1]["tiempo_optimo_min"] > r_c[-1]["tiempo_optimo_min"]

    def test_tiempo_total_tres_puntos_acumula_dos_segmentos(self):
        """t[2] debe ser la suma del segmento 0→1 y del 1→2."""
        r = estimar_tiempo_tramos(SUBIDA_3PTS, mes=6)
        t01 = r[1]["tiempo_optimo_min"]
        t12 = r[2]["tiempo_optimo_min"] - r[1]["tiempo_optimo_min"]
        assert t01 > 0
        assert t12 > 0
        assert abs(r[2]["tiempo_optimo_min"] - (t01 + t12)) < 0.01


# ── Factor altitud por segmento ───────────────────────────────────────────────

class TestFactorAltitudLocal:
    def test_baja_altitud_factor_1(self):
        puntos = [_punto(42.0, 0.0, 800), _punto(42.1, 0.0, 900)]
        r = estimar_tiempo_tramos(puntos, mes=6)
        # factor_alt = 1.0, factor_nieve = 1.0
        # horas_opt = horas_base * 1.0
        # horas_des = horas_opt * 1.15
        ratio = r[-1]["tiempo_desfavorable_min"] / r[-1]["tiempo_optimo_min"]
        assert abs(ratio - 1.15) < 0.01

    def test_alta_altitud_aumenta_tiempo(self):
        bajo  = [_punto(42.0, 0.0, 500),  _punto(42.1, 0.0, 500)]
        alto  = [_punto(42.0, 0.0, 3600), _punto(42.1, 0.0, 3600)]
        r_bajo = estimar_tiempo_tramos(bajo, mes=6)
        r_alto = estimar_tiempo_tramos(alto, mes=6)
        assert r_alto[-1]["tiempo_optimo_min"] > r_bajo[-1]["tiempo_optimo_min"]

    def test_factor_altitud_helper_umbrales(self):
        assert _factor_altitud(1000) == 1.0
        assert _factor_altitud(2600) == 1.12
        assert _factor_altitud(3100) == 1.22
        assert _factor_altitud(3600) == 1.35

    def test_segmentos_distintas_altitudes_acumulan_diferente(self):
        """Segundo segmento en mayor altitud debe añadir más tiempo."""
        pts_bajo  = [_punto(42.0, 0.0, 800), _punto(42.05, 0.0, 800), _punto(42.10, 0.0, 800)]
        pts_alto  = [_punto(42.0, 0.0, 800), _punto(42.05, 0.0, 800), _punto(42.10, 0.0, 3700)]
        r_bajo = estimar_tiempo_tramos(pts_bajo, mes=6)
        r_alto = estimar_tiempo_tramos(pts_alto, mes=6)
        # El tercer punto de pts_alto no tiene más distancia pero sí más desnivel y mayor alt
        assert r_alto[-1]["tiempo_optimo_min"] > r_bajo[-1]["tiempo_optimo_min"]


# ── Factor nieve ──────────────────────────────────────────────────────────────

class TestFactorNieve:
    def test_verano_sin_factor_nieve(self):
        """En verano desfav = optimo * 1.15 exactamente (sin nieve)."""
        r = estimar_tiempo_tramos(LLANO_2PTS, mes=7)
        ratio = r[-1]["tiempo_desfavorable_min"] / r[-1]["tiempo_optimo_min"]
        assert abs(ratio - 1.15) < 0.01

    def test_invierno_alta_montana_factor_nieve_130(self):
        """Invierno + altitud >3000m → factor_nieve=1.30."""
        r_v = estimar_tiempo_tramos(ALTA_MONTANA, mes=6)
        r_i = estimar_tiempo_tramos(ALTA_MONTANA, mes=1)
        # ratio invierno/verano en desfavorable
        ratio = r_i[-1]["tiempo_desfavorable_min"] / r_v[-1]["tiempo_desfavorable_min"]
        assert abs(ratio - 1.30) < 0.05

    def test_invierno_media_montana_factor_nieve_115(self):
        r_v = estimar_tiempo_tramos(PUNTOS_INVIERNO, mes=6)
        r_i = estimar_tiempo_tramos(PUNTOS_INVIERNO, mes=12)
        ratio = r_i[-1]["tiempo_desfavorable_min"] / r_v[-1]["tiempo_desfavorable_min"]
        assert abs(ratio - 1.15) < 0.05

    def test_meses_nieve_son_correctos(self):
        """Nov-Mar son meses de nieve; Abr-Oct no."""
        r_abr = estimar_tiempo_tramos(PUNTOS_INVIERNO, mes=4)
        r_nov = estimar_tiempo_tramos(PUNTOS_INVIERNO, mes=11)
        assert r_nov[-1]["tiempo_desfavorable_min"] > r_abr[-1]["tiempo_desfavorable_min"]


# ── Sin datos de elevación ────────────────────────────────────────────────────

class TestSinElevacion:
    def test_puntos_sin_elevacion_no_falla(self):
        puntos = [_punto_sin_elev(42.0, 0.0), _punto_sin_elev(42.1, 0.0)]
        r = estimar_tiempo_tramos(puntos, mes=6)
        assert len(r) == 2

    def test_sin_elevacion_solo_distancia_cuenta(self):
        """Sin elevación: sólo distancia horizontal, sin desnivel."""
        puntos = [_punto_sin_elev(42.0, 0.0), _punto_sin_elev(42.1, 0.0)]
        r = estimar_tiempo_tramos(puntos, mes=6)
        # dist ~11.1 km / 5 km/h = 2.22 h = 133 min aprox
        assert r[-1]["tiempo_optimo_min"] > 0

    def test_mezcla_con_y_sin_elevacion(self):
        """Segmento sin elevación trata desnivel como 0."""
        puntos = [
            _punto(42.0, 0.0, 1000),
            _punto_sin_elev(42.1, 0.0),
            _punto(42.2, 0.0, 1200),
        ]
        r = estimar_tiempo_tramos(puntos, mes=6)
        assert len(r) == 3
        assert r[1]["tiempo_optimo_min"] > 0
        assert r[2]["tiempo_optimo_min"] > r[1]["tiempo_optimo_min"]

    def test_todos_sin_elevacion_tiempo_positivo(self):
        puntos = [_punto_sin_elev(42.0, 0.0), _punto_sin_elev(42.05, 0.0),
                  _punto_sin_elev(42.10, 0.0)]
        r = estimar_tiempo_tramos(puntos, mes=6)
        assert r[-1]["tiempo_optimo_min"] > 0


# ── Casos límite ──────────────────────────────────────────────────────────────

class TestCasosLimite:
    def test_dos_puntos_minimo(self):
        r = estimar_tiempo_tramos(LLANO_2PTS, mes=6)
        assert len(r) == 2

    def test_puntos_identicos_tiempo_cero(self):
        """Dos puntos idénticos: distancia = 0, tiempo = 0."""
        puntos = [_punto(42.0, 0.0, 1000), _punto(42.0, 0.0, 1000)]
        r = estimar_tiempo_tramos(puntos, mes=6)
        assert r[-1]["tiempo_optimo_min"] == 0.0

    def test_sin_mes_usa_mes_actual(self):
        r = estimar_tiempo_tramos(LLANO_2PTS)
        assert r[-1]["tiempo_optimo_min"] > 0

    def test_todos_altitudes_none_altitud_max_default_cero(self):
        """Sin altitudes, altitud_max default=0, factor_nieve siempre 1.0 en invierno."""
        puntos = [_punto_sin_elev(42.0, 0.0), _punto_sin_elev(42.1, 0.0)]
        r_v = estimar_tiempo_tramos(puntos, mes=6)
        r_i = estimar_tiempo_tramos(puntos, mes=1)
        # Sin altitud: altitud_max=0, no supera 1500, factor_nieve=1.0
        assert r_v[-1]["tiempo_desfavorable_min"] == r_i[-1]["tiempo_desfavorable_min"]

    def test_track_largo_100_puntos(self):
        puntos = [_punto(42.0 + i * 0.01, 0.0, 1000 + i * 10) for i in range(100)]
        r = estimar_tiempo_tramos(puntos, mes=6)
        assert len(r) == 100
        assert r[-1]["km_acum"] > 0
        assert r[-1]["tiempo_optimo_min"] > 0


# ── Haversine interno ─────────────────────────────────────────────────────────

class TestHaversineKm:
    def test_misma_posicion_distancia_cero(self):
        p = {"lat": 42.0, "lon": 0.0}
        assert _haversine_km(p, p) == 0.0

    def test_1_grado_latitud_aprox_111_km(self):
        a = {"lat": 42.0, "lon": 0.0}
        b = {"lat": 43.0, "lon": 0.0}
        dist = _haversine_km(a, b)
        assert 110 < dist < 112

    def test_simetria(self):
        a = {"lat": 42.0, "lon": 0.0}
        b = {"lat": 42.5, "lon": 1.0}
        assert abs(_haversine_km(a, b) - _haversine_km(b, a)) < 1e-10


# ── Endpoint POST /api/estimacion/tramos ──────────────────────────────────────

class TestEndpointTramos:
    @pytest.fixture(autouse=True)
    def cliente(self):
        from main import app
        app.config["TESTING"] = True
        self.client = app.test_client()

    def _post(self, cuerpo):
        return self.client.post(
            "/api/estimacion/tramos",
            data=json.dumps(cuerpo),
            content_type="application/json",
        )

    def test_tres_puntos_validos_devuelve_200(self):
        r = self._post({"puntos": [
            {"lat": 42.0, "lon": 0.0, "elevacion_m": 1000},
            {"lat": 42.1, "lon": 0.0, "elevacion_m": 1200},
            {"lat": 42.2, "lon": 0.0, "elevacion_m": 1100},
        ], "mes": 6})
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data["ok"] is True
        assert "tramos" in data
        assert len(data["tramos"]) == 3

    def test_resultado_tiene_campos_correctos(self):
        r = self._post({"puntos": [
            {"lat": 42.0, "lon": 0.0, "elevacion_m": 1000},
            {"lat": 42.1, "lon": 0.0, "elevacion_m": 1200},
        ], "mes": 6})
        tramos = json.loads(r.data)["tramos"]
        for campo in ("indice", "km_acum", "alt_m", "lat", "lon",
                      "tiempo_optimo_min", "tiempo_desfavorable_min"):
            assert campo in tramos[0]
            assert campo in tramos[1]

    def test_primer_tramo_tiempo_cero(self):
        r = self._post({"puntos": [
            {"lat": 42.0, "lon": 0.0, "elevacion_m": 1000},
            {"lat": 42.1, "lon": 0.0, "elevacion_m": 1200},
        ], "mes": 6})
        assert json.loads(r.data)["tramos"][0]["tiempo_optimo_min"] == 0.0

    def test_sin_cuerpo_devuelve_400(self):
        r = self.client.post("/api/estimacion/tramos",
                             data="no-json", content_type="application/json")
        assert r.status_code == 400

    def test_sin_puntos_devuelve_400(self):
        r = self._post({"mes": 6})
        assert r.status_code == 400

    def test_puntos_no_lista_devuelve_400(self):
        r = self._post({"puntos": "no es lista", "mes": 6})
        assert r.status_code == 400

    def test_un_solo_punto_devuelve_400(self):
        r = self._post({"puntos": [{"lat": 42.0, "lon": 0.0, "elevacion_m": 1000}]})
        assert r.status_code == 400

    def test_punto_sin_lat_devuelve_400(self):
        r = self._post({"puntos": [
            {"lon": 0.0, "elevacion_m": 1000},
            {"lat": 42.1, "lon": 0.1, "elevacion_m": 1100},
        ]})
        assert r.status_code == 400

    def test_punto_sin_lon_devuelve_400(self):
        r = self._post({"puntos": [
            {"lat": 42.0, "elevacion_m": 1000},
            {"lat": 42.1, "lon": 0.1, "elevacion_m": 1100},
        ]})
        assert r.status_code == 400

    def test_mes_invalido_devuelve_400(self):
        r = self._post({"puntos": [
            {"lat": 42.0, "lon": 0.0, "elevacion_m": 1000},
            {"lat": 42.1, "lon": 0.0, "elevacion_m": 1200},
        ], "mes": 13})
        assert r.status_code == 400

    def test_mes_cero_devuelve_400(self):
        r = self._post({"puntos": [
            {"lat": 42.0, "lon": 0.0, "elevacion_m": 1000},
            {"lat": 42.1, "lon": 0.0, "elevacion_m": 1200},
        ], "mes": 0})
        assert r.status_code == 400

    def test_sin_mes_usa_mes_actual(self):
        r = self._post({"puntos": [
            {"lat": 42.0, "lon": 0.0, "elevacion_m": 1000},
            {"lat": 42.1, "lon": 0.0, "elevacion_m": 1200},
        ]})
        assert r.status_code == 200

    def test_puntos_sin_elevacion_acepta(self):
        r = self._post({"puntos": [
            {"lat": 42.0, "lon": 0.0, "elevacion_m": None},
            {"lat": 42.1, "lon": 0.0, "elevacion_m": None},
        ], "mes": 6})
        assert r.status_code == 200

    def test_puntos_sin_campo_elevacion_acepta(self):
        """elevacion_m es opcional."""
        r = self._post({"puntos": [
            {"lat": 42.0, "lon": 0.0},
            {"lat": 42.1, "lon": 0.0},
        ], "mes": 6})
        assert r.status_code == 200

    def test_limite_20001_puntos_devuelve_400(self):
        puntos = [{"lat": 42.0 + i * 0.0001, "lon": 0.0, "elevacion_m": 1000}
                  for i in range(20001)]
        r = self._post({"puntos": puntos, "mes": 6})
        assert r.status_code == 400

    def test_exactamente_20000_puntos_acepta(self):
        puntos = [{"lat": 42.0 + i * 0.00001, "lon": 0.0, "elevacion_m": 1000}
                  for i in range(20000)]
        r = self._post({"puntos": puntos, "mes": 6})
        assert r.status_code == 200

    def test_desfavorable_mayor_optimo_en_respuesta(self):
        r = self._post({"puntos": [
            {"lat": 42.0, "lon": 0.0, "elevacion_m": 1000},
            {"lat": 42.1, "lon": 0.0, "elevacion_m": 1500},
        ], "mes": 6})
        tramos = json.loads(r.data)["tramos"]
        assert tramos[1]["tiempo_desfavorable_min"] > tramos[1]["tiempo_optimo_min"]

    def test_km_acum_coherente_con_distancia_real(self):
        """~1 grado lat ≈ 111 km → ~11.1 km en 0.1 grado."""
        r = self._post({"puntos": [
            {"lat": 42.0, "lon": 0.0, "elevacion_m": 1000},
            {"lat": 42.1, "lon": 0.0, "elevacion_m": 1000},
        ], "mes": 6})
        km = json.loads(r.data)["tramos"][1]["km_acum"]
        assert 10 < km < 12
