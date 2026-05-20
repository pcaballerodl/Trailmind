"""Tests para src/itinerario/organizador.py y POST /api/itinerario/sugerir."""

import sys
import os
import math
import json
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from itinerario.organizador import (
    sugerir_checkpoints,
    _indice_en_tiempo,
    _ajustar_zona_plana,
    _pendiente_media,
    _poi_mas_cercano,
    _haversine_m,
    _demasiado_cerca,
    _crear,
    _deduplicar_y_ordenar,
    INTERVALO_COMIDA_MIN,
    DURACION_COMIDA_MIN,
    DURACION_CAMPAMENTO_MIN,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

def _tramo_simple(n=100, tiempo_total_min=300.0):
    """Genera n puntos con tiempo lineal y elevación plana."""
    tramos = []
    for i in range(n):
        frac = i / max(n - 1, 1)
        tramos.append({
            "indice": i,
            "km_acum": frac * 20.0,
            "alt_m": 1000.0,
            "lat": 42.0 + frac * 0.5,
            "lon": 0.0 + frac * 0.5,
            "tiempo_optimo_min":      frac * tiempo_total_min,
            "tiempo_desfavorable_min": frac * tiempo_total_min * 1.15,
        })
    return tramos


def _tramo_con_pendientes(n=50):
    """Genera tramos con pendientes variables."""
    tramos = []
    for i in range(n):
        frac = i / max(n - 1, 1)
        # Pendiente alta al principio y al final, plana en el medio
        if i < n // 3 or i > 2 * n // 3:
            alt = 1500 + i * 10
        else:
            alt = 1500 + (n // 3) * 10  # plana
        tramos.append({
            "indice": i,
            "km_acum": frac * 10.0,
            "alt_m": float(alt),
            "lat": 42.0 + frac * 0.2,
            "lon": 0.0,
            "tiempo_optimo_min": frac * 400.0,
            "tiempo_desfavorable_min": frac * 460.0,
        })
    return tramos


# ── Tests _haversine_m ────────────────────────────────────────────────────────

def test_haversine_cero():
    assert _haversine_m(42.0, 0.0, 42.0, 0.0) == pytest.approx(0.0, abs=0.01)


def test_haversine_positivo():
    d = _haversine_m(42.0, 0.0, 42.01, 0.0)
    assert d == pytest.approx(1113, rel=0.01)


def test_haversine_simetrico():
    a = _haversine_m(42.0, 0.0, 42.1, 0.1)
    b = _haversine_m(42.1, 0.1, 42.0, 0.0)
    assert a == pytest.approx(b, rel=1e-6)


# ── Tests _indice_en_tiempo ───────────────────────────────────────────────────

def test_indice_en_tiempo_inicio():
    tramos = _tramo_simple(10, 100.0)
    assert _indice_en_tiempo(tramos, "tiempo_optimo_min", 0) == 0


def test_indice_en_tiempo_fin():
    tramos = _tramo_simple(10, 100.0)
    idx = _indice_en_tiempo(tramos, "tiempo_optimo_min", 100.0)
    assert idx == 9


def test_indice_en_tiempo_mitad():
    tramos = _tramo_simple(11, 100.0)
    idx = _indice_en_tiempo(tramos, "tiempo_optimo_min", 50.0)
    assert idx == 5


def test_indice_en_tiempo_campo_desfavorable():
    tramos = _tramo_simple(11, 100.0)
    idx = _indice_en_tiempo(tramos, "tiempo_desfavorable_min", 57.5)
    assert 0 <= idx < len(tramos)


# ── Tests _pendiente_media ────────────────────────────────────────────────────

def test_pendiente_media_plana():
    tramos = _tramo_simple(10)
    p = _pendiente_media(tramos, 5)
    assert p == pytest.approx(0.0, abs=0.01)


def test_pendiente_media_primera():
    tramos = _tramo_simple(5)
    p = _pendiente_media(tramos, 0)
    assert p >= 0.0


def test_pendiente_media_ultima():
    tramos = _tramo_simple(5)
    p = _pendiente_media(tramos, 4)
    assert p >= 0.0


# ── Tests _ajustar_zona_plana ─────────────────────────────────────────────────

def test_ajustar_zona_plana_queda_en_rango():
    tramos = _tramo_con_pendientes(50)
    for idx in (0, 10, 25, 40, 49):
        resultado = _ajustar_zona_plana(tramos, idx)
        assert 0 <= resultado < len(tramos)


def test_ajustar_zona_plana_prefiere_pendiente_menor():
    tramos = _tramo_con_pendientes(50)
    # En la zona plana (middle), la pendiente ya es mínima
    idx_pendiente = 5
    resultado = _ajustar_zona_plana(tramos, idx_pendiente)
    pend_orig = _pendiente_media(tramos, idx_pendiente)
    pend_ajus = _pendiente_media(tramos, resultado)
    assert pend_ajus <= pend_orig + 1e-9


# ── Tests _poi_mas_cercano ────────────────────────────────────────────────────

def test_poi_mas_cercano_sin_pois():
    tramo = {"lat": 42.0, "lon": 0.0}
    assert _poi_mas_cercano(tramo, [], {"refugio"}) is None


def test_poi_mas_cercano_fuera_de_radio():
    tramo = {"lat": 42.0, "lon": 0.0}
    pois  = [{"tipo": "refugio", "lat": 43.0, "lon": 0.0, "nombre": "Lejano"}]
    assert _poi_mas_cercano(tramo, pois, {"refugio"}) is None


def test_poi_mas_cercano_dentro_radio():
    tramo = {"lat": 42.0, "lon": 0.0}
    pois  = [{"tipo": "refugio", "lat": 42.002, "lon": 0.0, "nombre": "Cercano"}]
    resultado = _poi_mas_cercano(tramo, pois, {"refugio"})
    assert resultado is not None
    assert resultado["tipo"] == "refugio"
    assert resultado["distancia_m"] < 800


def test_poi_mas_cercano_tipo_no_coincide():
    tramo = {"lat": 42.0, "lon": 0.0}
    pois  = [{"tipo": "fuente", "lat": 42.001, "lon": 0.0, "nombre": "Fuente"}]
    assert _poi_mas_cercano(tramo, pois, {"refugio"}) is None


def test_poi_mas_cercano_sin_coords():
    tramo = {"lat": None, "lon": None}
    pois  = [{"tipo": "refugio", "lat": 42.0, "lon": 0.0}]
    assert _poi_mas_cercano(tramo, pois, {"refugio"}) is None


# ── Tests _demasiado_cerca ────────────────────────────────────────────────────

def test_demasiado_cerca_si():
    # Con 10 puntos y 20 km totales, el paso es 2.22 km; usar umbral 3 km
    tramos = _tramo_simple(10)
    assert _demasiado_cerca(5, [4], tramos, min_km=3.0) is True


def test_demasiado_cerca_no():
    tramos = _tramo_simple(10)
    assert _demasiado_cerca(9, [0], tramos, min_km=1.0) is False


def test_demasiado_cerca_sin_referencias():
    tramos = _tramo_simple(10)
    assert _demasiado_cerca(5, [], tramos) is False


# ── Tests _crear ──────────────────────────────────────────────────────────────

def test_crear_campos_obligatorios():
    tramos = _tramo_simple(5)
    cp = _crear("comida", 2, tramos, "Parada", 45)
    assert cp["id"] == "comida_2"
    assert cp["tipo"] == "comida"
    assert cp["indice"] == 2
    assert cp["duracion_min"] == 45
    assert cp["auto"] is True
    assert cp["poi_cercano"] is None


def test_crear_con_poi():
    tramos = _tramo_simple(5)
    poi = {"tipo": "refugio", "nombre": "R1", "distancia_m": 200}
    cp = _crear("campamento", 3, tramos, "Camp", 480, poi_cercano=poi)
    assert cp["poi_cercano"]["tipo"] == "refugio"


# ── Tests _deduplicar_y_ordenar ───────────────────────────────────────────────

def test_deduplicar_elimina_duplicado():
    tramos = _tramo_simple(10)
    cps = [
        _crear("comida",    5, tramos, "A", 45),
        _crear("campamento", 5, tramos, "B", 480),
    ]
    resultado = _deduplicar_y_ordenar(cps)
    assert len(resultado) == 1
    assert resultado[0]["tipo"] == "campamento"


def test_deduplicar_ordena():
    tramos = _tramo_simple(10)
    cps = [
        _crear("comida", 8, tramos, "C", 45),
        _crear("comida", 3, tramos, "A", 45),
        _crear("comida", 5, tramos, "B", 45),
    ]
    resultado = _deduplicar_y_ordenar(cps)
    indices = [cp["indice"] for cp in resultado]
    assert indices == sorted(indices)


# ── Tests sugerir_checkpoints ─────────────────────────────────────────────────

def test_sugerir_lista_vacia():
    assert sugerir_checkpoints([]) == []


def test_sugerir_un_punto():
    assert sugerir_checkpoints([{"km_acum": 0, "tiempo_optimo_min": 0, "tiempo_desfavorable_min": 0}]) == []


def test_sugerir_tiempo_cero():
    tramos = [
        {"indice": 0, "km_acum": 0.0, "alt_m": 1000, "lat": 42.0, "lon": 0.0,
         "tiempo_optimo_min": 0.0, "tiempo_desfavorable_min": 0.0},
        {"indice": 1, "km_acum": 5.0, "alt_m": 1000, "lat": 42.1, "lon": 0.1,
         "tiempo_optimo_min": 0.0, "tiempo_desfavorable_min": 0.0},
    ]
    assert sugerir_checkpoints(tramos) == []


def test_sugerir_track_corto_sin_checkpoints():
    # Track de solo 2 horas → no hay parada de comida (umbral es 0.75 * 270 = 202.5)
    tramos = _tramo_simple(20, 120.0)
    resultado = sugerir_checkpoints(tramos, dias=1)
    assert resultado == []


def test_sugerir_track_largo_una_comida():
    # Track de 6 horas (360 min) → debería sugerir 1 comida a ~270 min
    tramos = _tramo_simple(50, 360.0)
    resultado = sugerir_checkpoints(tramos, dias=1)
    assert len(resultado) >= 1
    comidas = [cp for cp in resultado if cp["tipo"] == "comida"]
    assert len(comidas) >= 1


def test_sugerir_track_muy_largo_varias_comidas():
    # Track de 10 horas (600 min) → ~2 comidas
    tramos = _tramo_simple(100, 600.0)
    resultado = sugerir_checkpoints(tramos, dias=1)
    comidas = [cp for cp in resultado if cp["tipo"] == "comida"]
    assert len(comidas) >= 1


def test_sugerir_dos_dias_un_campamento():
    # Track de 2 días → 1 campamento al final del día 1
    tramos = _tramo_simple(100, 600.0)
    resultado = sugerir_checkpoints(tramos, dias=2)
    camps = [cp for cp in resultado if cp["tipo"] == "campamento"]
    assert len(camps) == 1


def test_sugerir_tres_dias_dos_campamentos():
    # Track de 3 días → 2 campamentos
    tramos = _tramo_simple(100, 900.0)
    resultado = sugerir_checkpoints(tramos, dias=3)
    camps = [cp for cp in resultado if cp["tipo"] == "campamento"]
    assert len(camps) == 2


def test_sugerir_orden_indices():
    tramos = _tramo_simple(100, 600.0)
    resultado = sugerir_checkpoints(tramos, dias=2)
    indices = [cp["indice"] for cp in resultado]
    assert indices == sorted(indices)


def test_sugerir_modo_desfavorable():
    tramos = _tramo_simple(100, 600.0)
    resultado = sugerir_checkpoints(tramos, dias=1, modo="desfavorable")
    assert isinstance(resultado, list)


def test_sugerir_con_pois():
    tramos = _tramo_simple(50, 360.0)
    pois = [{"tipo": "refugio", "lat": tramos[25]["lat"], "lon": tramos[25]["lon"], "nombre": "Refugio test"}]
    resultado = sugerir_checkpoints(tramos, pois=pois, dias=1)
    assert isinstance(resultado, list)


def test_sugerir_campos_checkpoint():
    tramos = _tramo_simple(100, 600.0)
    resultado = sugerir_checkpoints(tramos, dias=2)
    for cp in resultado:
        assert "id" in cp
        assert "tipo" in cp
        assert "indice" in cp
        assert "km_acum" in cp
        assert "duracion_min" in cp
        assert "auto" in cp
        assert cp["auto"] is True


def test_sugerir_campamento_duracion():
    tramos = _tramo_simple(100, 600.0)
    resultado = sugerir_checkpoints(tramos, dias=2)
    for cp in resultado:
        if cp["tipo"] == "campamento":
            assert cp["duracion_min"] == DURACION_CAMPAMENTO_MIN


def test_sugerir_comida_duracion():
    tramos = _tramo_simple(100, 600.0)
    resultado = sugerir_checkpoints(tramos, dias=1)
    for cp in resultado:
        if cp["tipo"] == "comida":
            assert cp["duracion_min"] == DURACION_COMIDA_MIN


def test_sugerir_sin_pois_none():
    tramos = _tramo_simple(50, 360.0)
    resultado = sugerir_checkpoints(tramos, pois=None, dias=1)
    assert isinstance(resultado, list)


def test_sugerir_dias_invalido_corrige():
    tramos = _tramo_simple(50, 360.0)
    resultado = sugerir_checkpoints(tramos, dias=0)
    # Con dias=0, internamente se corrige a 1
    assert isinstance(resultado, list)


# ── Tests HTTP POST /api/itinerario/sugerir ───────────────────────────────────

@pytest.fixture
def cliente():
    from main import app
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_endpoint_ok(cliente):
    tramos = _tramo_simple(50, 360.0)
    r = cliente.post(
        "/api/itinerario/sugerir",
        data=json.dumps({"tramos": tramos, "dias": 1}),
        content_type="application/json",
    )
    assert r.status_code == 200
    data = r.get_json()
    assert data["ok"] is True
    assert "checkpoints" in data
    assert isinstance(data["checkpoints"], list)


def test_endpoint_sin_cuerpo(cliente):
    r = cliente.post("/api/itinerario/sugerir", data="", content_type="application/json")
    assert r.status_code == 400


def test_endpoint_tramos_invalidos(cliente):
    r = cliente.post(
        "/api/itinerario/sugerir",
        data=json.dumps({"tramos": "no-lista"}),
        content_type="application/json",
    )
    assert r.status_code == 400


def test_endpoint_tramos_un_elemento(cliente):
    r = cliente.post(
        "/api/itinerario/sugerir",
        data=json.dumps({"tramos": [_tramo_simple(2)[0]]}),
        content_type="application/json",
    )
    assert r.status_code == 400


def test_endpoint_dias_invalido(cliente):
    tramos = _tramo_simple(10, 100.0)
    r = cliente.post(
        "/api/itinerario/sugerir",
        data=json.dumps({"tramos": tramos, "dias": 99}),
        content_type="application/json",
    )
    assert r.status_code == 400


def test_endpoint_modo_invalido(cliente):
    tramos = _tramo_simple(10, 100.0)
    r = cliente.post(
        "/api/itinerario/sugerir",
        data=json.dumps({"tramos": tramos, "modo": "supervelocidad"}),
        content_type="application/json",
    )
    assert r.status_code == 400


def test_endpoint_modo_desfavorable(cliente):
    tramos = _tramo_simple(50, 360.0)
    r = cliente.post(
        "/api/itinerario/sugerir",
        data=json.dumps({"tramos": tramos, "dias": 1, "modo": "desfavorable"}),
        content_type="application/json",
    )
    assert r.status_code == 200
    assert r.get_json()["ok"] is True


def test_endpoint_dos_dias(cliente):
    tramos = _tramo_simple(100, 600.0)
    r = cliente.post(
        "/api/itinerario/sugerir",
        data=json.dumps({"tramos": tramos, "dias": 2}),
        content_type="application/json",
    )
    data = r.get_json()
    assert data["ok"] is True
    camps = [cp for cp in data["checkpoints"] if cp["tipo"] == "campamento"]
    assert len(camps) == 1


def test_endpoint_pois_invalidos(cliente):
    tramos = _tramo_simple(10, 100.0)
    r = cliente.post(
        "/api/itinerario/sugerir",
        data=json.dumps({"tramos": tramos, "pois": "no-lista"}),
        content_type="application/json",
    )
    assert r.status_code == 400


def test_endpoint_pois_vacios(cliente):
    tramos = _tramo_simple(50, 360.0)
    r = cliente.post(
        "/api/itinerario/sugerir",
        data=json.dumps({"tramos": tramos, "pois": []}),
        content_type="application/json",
    )
    assert r.status_code == 200
    assert r.get_json()["ok"] is True
