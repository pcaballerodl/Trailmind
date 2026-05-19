import io
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gpx import parsear_gpx

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def abrir_fixture(nombre):
    ruta = os.path.join(FIXTURE_DIR, nombre)
    with open(ruta, "rb") as f:
        contenido = f.read()
    archivo = io.BytesIO(contenido)
    archivo.filename = nombre
    return archivo


class TestParsearGpx:
    def test_devuelve_claves_esperadas(self):
        archivo = abrir_fixture("track_simple.gpx")
        datos = parsear_gpx(archivo)
        claves = [
            "nombre_track", "total_puntos", "distancia_km",
            "desnivel_positivo_m", "desnivel_negativo_m",
            "altitud_max_m", "altitud_min_m", "altitud_media_m",
            "tiene_timestamps", "puntos",
        ]
        for clave in claves:
            assert clave in datos, f"Falta la clave: {clave}"

    def test_nombre_track(self):
        archivo = abrir_fixture("track_simple.gpx")
        datos = parsear_gpx(archivo)
        assert datos["nombre_track"] == "Track de prueba"

    def test_total_puntos(self):
        archivo = abrir_fixture("track_simple.gpx")
        datos = parsear_gpx(archivo)
        assert datos["total_puntos"] == 5

    def test_desnivel_positivo(self):
        archivo = abrir_fixture("track_simple.gpx")
        datos = parsear_gpx(archivo)
        # 200 + 300 = 500 m de D+
        assert datos["desnivel_positivo_m"] == pytest.approx(500.0, abs=1.0)

    def test_desnivel_negativo(self):
        archivo = abrir_fixture("track_simple.gpx")
        datos = parsear_gpx(archivo)
        # 100 + 400 = 500 m de D-
        assert datos["desnivel_negativo_m"] == pytest.approx(500.0, abs=1.0)

    def test_altitud_maxima(self):
        archivo = abrir_fixture("track_simple.gpx")
        datos = parsear_gpx(archivo)
        assert datos["altitud_max_m"] == pytest.approx(1500.0, abs=0.1)

    def test_altitud_minima(self):
        archivo = abrir_fixture("track_simple.gpx")
        datos = parsear_gpx(archivo)
        assert datos["altitud_min_m"] == pytest.approx(1000.0, abs=0.1)

    def test_distancia_positiva(self):
        archivo = abrir_fixture("track_simple.gpx")
        datos = parsear_gpx(archivo)
        assert datos["distancia_km"] > 0

    def test_sin_timestamps(self):
        archivo = abrir_fixture("track_simple.gpx")
        datos = parsear_gpx(archivo)
        assert datos["tiene_timestamps"] is False
        assert all(p["timestamp"] is None for p in datos["puntos"])

    def test_estructura_puntos(self):
        archivo = abrir_fixture("track_simple.gpx")
        datos = parsear_gpx(archivo)
        for punto in datos["puntos"]:
            assert "lat" in punto
            assert "lon" in punto
            assert "elevacion_m" in punto
            assert "timestamp" in punto


class TestErrores:
    def test_extension_incorrecta(self):
        archivo = io.BytesIO(b"<gpx/>")
        archivo.filename = "track.txt"
        with pytest.raises(ValueError, match="extensión"):
            parsear_gpx(archivo)

    def test_xml_invalido(self):
        archivo = io.BytesIO(b"esto no es xml")
        archivo.filename = "track.gpx"
        with pytest.raises(ValueError, match="válido"):
            parsear_gpx(archivo)

    def test_gpx_sin_puntos(self):
        gpx_vacio = b"""<?xml version="1.0"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <trk><trkseg></trkseg></trk>
</gpx>"""
        archivo = io.BytesIO(gpx_vacio)
        archivo.filename = "vacio.gpx"
        with pytest.raises(ValueError, match="puntos"):
            parsear_gpx(archivo)
