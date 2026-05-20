from datetime import datetime, date
from flask import Flask, request, jsonify, send_from_directory
from gpx import parsear_gpx
from weather import obtener_prevision

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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
