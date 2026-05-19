from flask import Flask, request, jsonify
from gpx import parsear_gpx

app = Flask(__name__)


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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
