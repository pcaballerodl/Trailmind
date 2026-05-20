import sys
import os
import pytest
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from estimacion.calculadora import estimar_tiempo

# ── Track de referencia: ruta alpina media ─────────────────────────────────────
TRACK_ALPINO = {
    "distancia_km": 12.0,
    "desnivel_positivo_m": 900,
    "desnivel_negativo_m": 900,
    "altitud_media_m": 2200,
    "altitud_max_m": 2800,
    "tramos_duros_pct": 15.0,
}

TRACK_LLANO = {
    "distancia_km": 10.0,
    "desnivel_positivo_m": 100,
    "desnivel_negativo_m": 100,
    "altitud_media_m": 500,
    "altitud_max_m": 600,
    "tramos_duros_pct": 0.0,
}

TRACK_MINIMO = {
    "distancia_km": 1.0,
    "desnivel_positivo_m": 50,
    "desnivel_negativo_m": 50,
    "altitud_media_m": 300,
    "altitud_max_m": 350,
}

TRACK_ALTA_MONTANYA = {
    "distancia_km": 8.0,
    "desnivel_positivo_m": 1200,
    "desnivel_negativo_m": 1200,
    "altitud_media_m": 3600,
    "altitud_max_m": 4000,
    "tramos_duros_pct": 30.0,
}


class TestEstructuraResultado:
    def test_devuelve_optimo_y_desfavorable(self):
        r = estimar_tiempo(TRACK_ALPINO, mes=6)
        assert "optimo" in r
        assert "desfavorable" in r

    def test_devuelve_factores(self):
        r = estimar_tiempo(TRACK_ALPINO, mes=6)
        assert "factores" in r
        f = r["factores"]
        assert "factor_altitud" in f
        assert "factor_nieve" in f
        assert "con_datos_pendiente" in f

    def test_formato_tiempo_tiene_horas_minutos_total(self):
        r = estimar_tiempo(TRACK_ALPINO, mes=6)
        for clave in ("optimo", "desfavorable"):
            t = r[clave]
            assert "horas" in t
            assert "minutos" in t
            assert "total_min" in t

    def test_minutos_entre_0_y_59(self):
        r = estimar_tiempo(TRACK_ALPINO, mes=6)
        for clave in ("optimo", "desfavorable"):
            assert 0 <= r[clave]["minutos"] <= 59

    def test_total_min_coherente_con_horas_y_minutos(self):
        r = estimar_tiempo(TRACK_ALPINO, mes=6)
        for clave in ("optimo", "desfavorable"):
            t = r[clave]
            assert t["total_min"] == t["horas"] * 60 + t["minutos"]

    def test_desfavorable_mayor_o_igual_a_optimo(self):
        r = estimar_tiempo(TRACK_ALPINO, mes=6)
        assert r["desfavorable"]["total_min"] >= r["optimo"]["total_min"]


class TestFormulaNaismith:
    def test_track_llano_mas_rapido_que_alpino(self):
        r_llano = estimar_tiempo(TRACK_LLANO, mes=6)
        r_alpino = estimar_tiempo(TRACK_ALPINO, mes=6)
        assert r_llano["optimo"]["total_min"] < r_alpino["optimo"]["total_min"]

    def test_mayor_distancia_mayor_tiempo(self):
        track_corto = {**TRACK_LLANO, "distancia_km": 5.0}
        track_largo = {**TRACK_LLANO, "distancia_km": 20.0}
        r_corto = estimar_tiempo(track_corto, mes=6)
        r_largo = estimar_tiempo(track_largo, mes=6)
        assert r_largo["optimo"]["total_min"] > r_corto["optimo"]["total_min"]

    def test_mayor_desnivel_mayor_tiempo(self):
        track_suave = {**TRACK_LLANO, "desnivel_positivo_m": 100, "desnivel_negativo_m": 100}
        track_empinado = {**TRACK_LLANO, "desnivel_positivo_m": 1500, "desnivel_negativo_m": 1500}
        r_suave = estimar_tiempo(track_suave, mes=6)
        r_empinado = estimar_tiempo(track_empinado, mes=6)
        assert r_empinado["optimo"]["total_min"] > r_suave["optimo"]["total_min"]

    def test_resultado_positivo_no_cero(self):
        r = estimar_tiempo(TRACK_MINIMO, mes=6)
        assert r["optimo"]["total_min"] > 0

    def test_track_extremadamente_corto_no_da_cero(self):
        track = {
            "distancia_km": 0.0,
            "desnivel_positivo_m": 0,
            "desnivel_negativo_m": 0,
            "altitud_media_m": 100,
            "altitud_max_m": 100,
        }
        r = estimar_tiempo(track, mes=6)
        assert r["optimo"]["total_min"] > 0  # max(0.1, ...) garantiza mínimo


class TestFactorAltitud:
    def test_altitud_baja_factor_1(self):
        track = {**TRACK_LLANO, "altitud_media_m": 1000, "altitud_max_m": 1200}
        r = estimar_tiempo(track, mes=6)
        assert r["factores"]["factor_altitud"] == 1.0

    def test_altitud_media_2700_factor_112(self):
        track = {**TRACK_LLANO, "altitud_media_m": 2700, "altitud_max_m": 3000}
        r = estimar_tiempo(track, mes=6)
        assert r["factores"]["factor_altitud"] == 1.12

    def test_altitud_3200_factor_122(self):
        track = {**TRACK_LLANO, "altitud_media_m": 3200, "altitud_max_m": 3500}
        r = estimar_tiempo(track, mes=6)
        assert r["factores"]["factor_altitud"] == 1.22

    def test_altitud_alta_4000_factor_135(self):
        track = {**TRACK_ALTA_MONTANYA}
        r = estimar_tiempo(track, mes=6)
        assert r["factores"]["factor_altitud"] == 1.35

    def test_alta_altitud_hace_tiempo_mayor(self):
        track_bajo = {**TRACK_LLANO, "altitud_media_m": 500, "altitud_max_m": 700}
        track_alto = {**TRACK_LLANO, "altitud_media_m": 3600, "altitud_max_m": 4000}
        r_bajo = estimar_tiempo(track_bajo, mes=6)
        r_alto = estimar_tiempo(track_alto, mes=6)
        assert r_alto["optimo"]["total_min"] > r_bajo["optimo"]["total_min"]


class TestFactorNieve:
    def test_verano_factor_nieve_1(self):
        r = estimar_tiempo(TRACK_ALPINO, mes=7)
        assert r["factores"]["factor_nieve"] == 1.0

    def test_invierno_altitud_alta_factor_130(self):
        track = {**TRACK_ALPINO, "altitud_max_m": 3500}
        r = estimar_tiempo(track, mes=1)
        assert r["factores"]["factor_nieve"] == 1.30

    def test_invierno_altitud_media_factor_115(self):
        track = {**TRACK_ALPINO, "altitud_max_m": 2500}
        r = estimar_tiempo(track, mes=12)
        assert r["factores"]["factor_nieve"] == 1.15

    def test_invierno_altitud_baja_factor_107(self):
        track = {**TRACK_LLANO, "altitud_max_m": 1700}
        r = estimar_tiempo(track, mes=2)
        assert r["factores"]["factor_nieve"] == 1.07

    def test_invierno_altitud_muy_baja_sin_penalizacion(self):
        track = {**TRACK_LLANO, "altitud_max_m": 800}
        r = estimar_tiempo(track, mes=12)
        assert r["factores"]["factor_nieve"] == 1.0

    def test_meses_frontera(self):
        track = {**TRACK_ALPINO, "altitud_max_m": 2500}
        # noviembre y marzo son meses de nieve
        assert estimar_tiempo(track, mes=11)["factores"]["factor_nieve"] > 1.0
        assert estimar_tiempo(track, mes=3)["factores"]["factor_nieve"] > 1.0
        # abril no
        assert estimar_tiempo(track, mes=4)["factores"]["factor_nieve"] == 1.0

    def test_invierno_hace_desfavorable_peor_que_verano(self):
        r_verano = estimar_tiempo(TRACK_ALPINO, mes=7)
        r_invierno = estimar_tiempo(TRACK_ALPINO, mes=1)
        assert r_invierno["desfavorable"]["total_min"] > r_verano["desfavorable"]["total_min"]


class TestTramosDuros:
    def test_tramos_duros_aumentan_tiempo(self):
        track_suave = {**TRACK_ALPINO, "tramos_duros_pct": 0.0}
        track_duro = {**TRACK_ALPINO, "tramos_duros_pct": 50.0}
        r_suave = estimar_tiempo(track_suave, mes=6)
        r_duro = estimar_tiempo(track_duro, mes=6)
        assert r_duro["optimo"]["total_min"] > r_suave["optimo"]["total_min"]

    def test_sin_tramos_duros_no_penaliza(self):
        track = {**TRACK_ALPINO, "tramos_duros_pct": 0.0}
        r = estimar_tiempo(track, mes=6)
        assert r["factores"]["con_datos_pendiente"] is False

    def test_tramos_duros_activa_flag(self):
        track = {**TRACK_ALPINO, "tramos_duros_pct": 20.0}
        r = estimar_tiempo(track, mes=6)
        assert r["factores"]["con_datos_pendiente"] is True

    def test_tramos_duros_none_no_falla(self):
        track = {**TRACK_ALPINO}
        track.pop("tramos_duros_pct", None)
        r = estimar_tiempo(track, mes=6)
        assert r["factores"]["con_datos_pendiente"] is False

    def test_tramos_duros_none_explícito(self):
        track = {**TRACK_ALPINO, "tramos_duros_pct": None}
        r = estimar_tiempo(track, mes=6)
        assert r["factores"]["con_datos_pendiente"] is False


class TestMesPorDefecto:
    def test_sin_mes_usa_mes_actual(self):
        # Solo verificamos que no lanza excepción
        r = estimar_tiempo(TRACK_ALPINO)
        assert r["optimo"]["total_min"] > 0


class TestEndpointEstimacion:
    @pytest.fixture(autouse=True)
    def cliente(self):
        from main import app
        app.config["TESTING"] = True
        self.client = app.test_client()

    def _post(self, cuerpo):
        return self.client.post(
            "/api/estimacion/tiempo",
            data=json.dumps(cuerpo),
            content_type="application/json",
        )

    def test_track_valido_devuelve_200(self):
        r = self._post({"track": TRACK_ALPINO, "mes": 6})
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data["ok"] is True
        assert "estimacion" in data

    def test_respuesta_tiene_optimo_y_desfavorable(self):
        r = self._post({"track": TRACK_ALPINO, "mes": 6})
        data = json.loads(r.data)
        assert "optimo" in data["estimacion"]
        assert "desfavorable" in data["estimacion"]

    def test_sin_cuerpo_devuelve_400(self):
        r = self.client.post("/api/estimacion/tiempo", data="no-json", content_type="application/json")
        assert r.status_code == 400

    def test_sin_track_devuelve_400(self):
        r = self._post({"mes": 6})
        assert r.status_code == 400
        assert "track" in json.loads(r.data)["error"]

    def test_faltan_campos_obligatorios_devuelve_400(self):
        r = self._post({"track": {"distancia_km": 10.0}})
        assert r.status_code == 400

    def test_mes_invalido_devuelve_400(self):
        r = self._post({"track": TRACK_ALPINO, "mes": 13})
        assert r.status_code == 400

    def test_mes_cero_devuelve_400(self):
        r = self._post({"track": TRACK_ALPINO, "mes": 0})
        assert r.status_code == 400

    def test_mes_string_invalido_devuelve_400(self):
        r = self._post({"track": TRACK_ALPINO, "mes": "enero"})
        assert r.status_code == 400

    def test_sin_mes_usa_mes_actual_y_devuelve_200(self):
        r = self._post({"track": TRACK_ALPINO})
        assert r.status_code == 200
        assert json.loads(r.data)["ok"] is True

    def test_track_sin_altitud_media_devuelve_200(self):
        track = {
            "distancia_km": 10.0,
            "desnivel_positivo_m": 500,
            "desnivel_negativo_m": 500,
        }
        r = self._post({"track": track, "mes": 6})
        assert r.status_code == 200

    def test_track_con_valores_cero_devuelve_200(self):
        track = {
            "distancia_km": 0.0,
            "desnivel_positivo_m": 0,
            "desnivel_negativo_m": 0,
        }
        r = self._post({"track": track, "mes": 6})
        assert r.status_code == 200

    def test_track_no_es_dict_devuelve_400(self):
        r = self._post({"track": "no es un dict", "mes": 6})
        assert r.status_code == 400
