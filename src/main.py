import json
from datetime import datetime, date
from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context
from gpx import parsear_gpx
from weather import obtener_prevision
from ai import generar_plan_stream
from ai.prompt import construir_sistema, construir_usuario
from overpass import buscar_pois
from estimacion import estimar_tiempo, estimar_tiempo_tramos

app = Flask(__name__, static_folder="static", static_url_path="/static")


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/gpx/subir", methods=["POST"])
def subir_gpx():
    if "archivo" not in request.files:
        return jsonify({"ok": False, "error": "No se envió ningún archivo"}), 400

    archivo = request.files["archivo"]

    if archivo.filename == "":
        return jsonify({"ok": False, "error": "El archivo está vacío"}), 400

    try:
        datos = parsear_gpx(archivo)
        return jsonify({"ok": True, "datos": datos})
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception:
        return jsonify({"ok": False, "error": "Error inesperado al procesar el archivo"}), 500


@app.route("/api/meteo/prevision", methods=["GET"])
def prevision_meteo():
    # Validar parámetros obligatorios
    try:
        lat = float(request.args.get("lat", ""))
        lon = float(request.args.get("lon", ""))
    except ValueError:
        return jsonify({"ok": False, "error": "lat y lon deben ser números válidos"}), 400

    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        return jsonify({"ok": False, "error": "Coordenadas fuera de rango"}), 400

    fecha_str = request.args.get("fecha", "")
    try:
        fecha_obj = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"ok": False, "error": "Fecha inválida, usa formato YYYY-MM-DD"}), 400

    hoy = date.today()
    if fecha_obj < hoy:
        return jsonify({"ok": False, "error": "Solo se puede consultar la previsión de los próximos 16 días"}), 400
    if (fecha_obj - hoy).days > 16:
        return jsonify({"ok": False, "error": "La fecha no puede ser más de 16 días en el futuro"}), 400

    try:
        dias = int(request.args.get("dias", 7))
        if not (1 <= dias <= 16):
            raise ValueError
    except ValueError:
        return jsonify({"ok": False, "error": "dias debe ser un entero entre 1 y 16"}), 400

    if (fecha_obj - hoy).days + dias > 16:
        return jsonify({"ok": False, "error": "El rango de días solicitado excede los 16 días de previsión disponibles"}), 400

    try:
        prevision = obtener_prevision(lat, lon, fecha_str, dias)
        return jsonify({"ok": True, "prevision": prevision})
    except RuntimeError as e:
        return jsonify({"ok": False, "error": str(e)}), 502
    except Exception:
        return jsonify({"ok": False, "error": "Error inesperado al obtener la previsión"}), 500


@app.route("/api/ia/plan", methods=["POST"])
def generar_plan_ia():
    cuerpo = request.get_json(silent=True)
    if not cuerpo:
        return jsonify({"ok": False, "error": "Cuerpo JSON inválido"}), 400

    track = cuerpo.get("track")
    if not track:
        return jsonify({"ok": False, "error": "Falta el campo 'track'"}), 400

    preferencias = cuerpo.get("preferencias", {})
    nivel = preferencias.get("nivel", "")
    if nivel not in ("principiante", "intermedio", "avanzado", "experto"):
        return jsonify({"ok": False, "error": "nivel debe ser: principiante, intermedio, avanzado o experto"}), 400

    try:
        dias = int(preferencias.get("dias", 1))
        if not (1 <= dias <= 14):
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"ok": False, "error": "dias debe ser un entero entre 1 y 14"}), 400

    try:
        personas = int(preferencias.get("personas", 1))
        if not (1 <= personas <= 20):
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"ok": False, "error": "personas debe ser un entero entre 1 y 20"}), 400

    prevision = cuerpo.get("prevision")
    preferencias_limpias = {"dias": dias, "nivel": nivel, "personas": personas}

    prompt_sistema = construir_sistema()
    prompt_usuario = construir_usuario(track, prevision, preferencias_limpias)

    def stream_eventos():
        try:
            for chunk in generar_plan_stream(prompt_sistema, prompt_usuario):
                yield f"data: {json.dumps({'tipo': 'chunk', 'texto': chunk})}\n\n"
            yield f"data: {json.dumps({'tipo': 'fin'})}\n\n"
        except RuntimeError as e:
            yield f"data: {json.dumps({'tipo': 'error', 'mensaje': str(e)})}\n\n"
        except Exception:
            yield f"data: {json.dumps({'tipo': 'error', 'mensaje': 'Error inesperado al generar el plan'})}\n\n"

    return Response(
        stream_with_context(stream_eventos()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/api/mapa/puntos-interes", methods=["POST"])
def puntos_interes():
    cuerpo = request.get_json(silent=True)
    if not cuerpo:
        return jsonify({"ok": False, "error": "Cuerpo JSON inválido"}), 400

    bbox = cuerpo.get("bbox")
    if not isinstance(bbox, dict) or not all(
        k in bbox for k in ("min_lat", "max_lat", "min_lon", "max_lon")
    ):
        return jsonify({"ok": False, "error": "Falta o es inválido el campo 'bbox'"}), 400

    try:
        radio_m = int(cuerpo.get("radio_m", 1000))
        if not (100 <= radio_m <= 5000):
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"ok": False, "error": "radio_m debe ser un entero entre 100 y 5000"}), 400

    tipos = cuerpo.get("tipos", ["fuente", "refugio"])
    tipos_validos = {"fuente", "refugio"}
    if not isinstance(tipos, list) or not tipos or not all(t in tipos_validos for t in tipos):
        return jsonify({"ok": False, "error": "tipos debe ser una lista con 'fuente' y/o 'refugio'"}), 400

    try:
        pois = buscar_pois(bbox, radio_m, tipos)
        return jsonify({"ok": True, "pois": pois})
    except RuntimeError as e:
        return jsonify({"ok": False, "error": str(e)}), 502
    except Exception:
        return jsonify({"ok": False, "error": "Error inesperado al consultar puntos de interés"}), 500


@app.route("/api/estimacion/tiempo", methods=["POST"])
def calcular_estimacion():
    cuerpo = request.get_json(silent=True)
    if not cuerpo:
        return jsonify({"ok": False, "error": "Cuerpo JSON inválido"}), 400

    track = cuerpo.get("track")
    if not track or not isinstance(track, dict):
        return jsonify({"ok": False, "error": "Falta el campo 'track'"}), 400

    campos_requeridos = ["distancia_km", "desnivel_positivo_m", "desnivel_negativo_m"]
    if not all(k in track for k in campos_requeridos):
        return jsonify({"ok": False, "error": "Faltan campos obligatorios en 'track'"}), 400

    mes = cuerpo.get("mes")
    if mes is not None:
        try:
            mes = int(mes)
            if not (1 <= mes <= 12):
                raise ValueError
        except (ValueError, TypeError):
            return jsonify({"ok": False, "error": "mes debe ser un entero entre 1 y 12"}), 400

    try:
        estimacion = estimar_tiempo(track, mes)
        return jsonify({"ok": True, "estimacion": estimacion})
    except Exception:
        return jsonify({"ok": False, "error": "Error al calcular la estimación"}), 500


@app.route("/api/estimacion/tramos", methods=["POST"])
def calcular_tramos():
    cuerpo = request.get_json(silent=True)
    if not cuerpo:
        return jsonify({"ok": False, "error": "Cuerpo JSON inválido"}), 400

    puntos = cuerpo.get("puntos")
    if not isinstance(puntos, list) or len(puntos) < 2:
        return jsonify({"ok": False, "error": "puntos debe ser una lista con al menos 2 elementos"}), 400

    if len(puntos) > 20000:
        return jsonify({"ok": False, "error": "puntos no puede superar los 20000 elementos"}), 400

    for i, p in enumerate(puntos):
        if not isinstance(p, dict) or "lat" not in p or "lon" not in p:
            return jsonify({"ok": False, "error": f"El punto {i} no tiene lat/lon"}), 400

    mes = cuerpo.get("mes")
    if mes is not None:
        try:
            mes = int(mes)
            if not (1 <= mes <= 12):
                raise ValueError
        except (ValueError, TypeError):
            return jsonify({"ok": False, "error": "mes debe ser un entero entre 1 y 12"}), 400

    try:
        tramos = estimar_tiempo_tramos(puntos, mes)
        return jsonify({"ok": True, "tramos": tramos})
    except Exception:
        return jsonify({"ok": False, "error": "Error al calcular los tramos"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
