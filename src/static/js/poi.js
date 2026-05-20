window.TrailMind = window.TrailMind || {};

window.TrailMind.poi = (function () {

  var _bbox = null;
  var _pois = [];   // último resultado de búsqueda

  function establecerBbox(puntos) {
    if (!puntos || puntos.length === 0) return;
    var lats = puntos.map(function (p) { return p.lat; });
    var lons = puntos.map(function (p) { return p.lon; });
    _bbox = {
      min_lat: Math.min.apply(null, lats),
      max_lat: Math.max.apply(null, lats),
      min_lon: Math.min.apply(null, lons),
      max_lon: Math.max.apply(null, lons),
    };
  }

  function buscar() {
    if (!_bbox) return;

    var tipos = _getTiposActivos();
    if (tipos.length === 0) {
      var poiError = document.getElementById("poi-error");
      if (poiError) {
        poiError.textContent = "Selecciona al menos un tipo";
        poiError.classList.remove("oculto");
      }
      return;
    }

    var radio = parseInt(document.getElementById("poi-radio").value, 10) || 1000;
    var btnBuscar = document.getElementById("btn-buscar-poi");
    var poiSpinner = document.getElementById("poi-spinner");
    var poiError = document.getElementById("poi-error");
    var poiContador = document.getElementById("poi-contador");

    if (btnBuscar) btnBuscar.disabled = true;
    if (poiSpinner) poiSpinner.classList.remove("oculto");
    if (poiError) poiError.classList.add("oculto");
    if (poiContador) poiContador.classList.add("oculto");

    TrailMind.mapa.limpiarPois();

    fetch("/api/mapa/puntos-interes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ bbox: _bbox, radio_m: radio, tipos: tipos }),
    })
      .then(function (r) { return r.json(); })
      .then(function (json) {
        if (json.ok) {
          _pois = json.pois;
          TrailMind.mapa.mostrarPois(json.pois);
          _mostrarContador(json.pois);
        } else {
          if (poiError) {
            poiError.textContent = json.error || "Error al buscar puntos de interés";
            poiError.classList.remove("oculto");
          }
        }
      })
      .catch(function () {
        if (poiError) {
          poiError.textContent = "No se pudo conectar con el servidor";
          poiError.classList.remove("oculto");
        }
      })
      .then(function () {
        if (btnBuscar) btnBuscar.disabled = false;
        if (poiSpinner) poiSpinner.classList.add("oculto");
      });
  }

  function obtenerPois() { return _pois; }

  function limpiar() {
    _bbox = null;
    _pois = [];
    var contador = document.getElementById("poi-contador");
    if (contador) contador.classList.add("oculto");
    var error = document.getElementById("poi-error");
    if (error) { error.classList.add("oculto"); error.textContent = ""; }
    if (TrailMind.mapa && TrailMind.mapa.limpiarPois) {
      TrailMind.mapa.limpiarPois();
    }
  }

  // Devuelve array de tipos seleccionados según el estado de los toggles
  function _getTiposActivos() {
    var tipos = [];
    var btnFuentes = document.getElementById("toggle-fuentes");
    var btnRefugios = document.getElementById("toggle-refugios");
    if (btnFuentes && btnFuentes.classList.contains("activo")) tipos.push("fuente");
    if (btnRefugios && btnRefugios.classList.contains("activo")) tipos.push("refugio");
    return tipos;
  }

  function _mostrarContador(pois) {
    var contador = document.getElementById("poi-contador");
    if (!contador) return;
    var nFuentes = pois.filter(function (p) { return p.tipo === "fuente"; }).length;
    var nRefugios = pois.filter(function (p) { return p.tipo === "refugio"; }).length;
    var partes = [];
    if (nFuentes > 0) partes.push(nFuentes + " 💧");
    if (nRefugios > 0) partes.push(nRefugios + " ⛺");
    contador.textContent = partes.length > 0
      ? "Encontrado: " + partes.join(" · ")
      : "Sin resultados";
    contador.classList.remove("oculto");
  }

  return {
    establecerBbox: establecerBbox,
    buscar:         buscar,
    limpiar:        limpiar,
    obtenerPois:    obtenerPois,
  };

})();
