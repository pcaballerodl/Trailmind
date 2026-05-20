window.TrailMind = window.TrailMind || {};

window.TrailMind.poi = (function () {

  var _bbox = null;

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

    var radio = parseInt(document.getElementById("poi-radio").value, 10) || 1000;
    var btnBuscar = document.getElementById("btn-buscar-poi");
    var poiSpinner = document.getElementById("poi-spinner");
    var poiError = document.getElementById("poi-error");

    if (btnBuscar) btnBuscar.disabled = true;
    if (poiSpinner) poiSpinner.classList.remove("oculto");
    if (poiError) poiError.classList.add("oculto");

    TrailMind.mapa.limpiarPois();

    fetch("/api/mapa/puntos-interes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ bbox: _bbox, radio_m: radio, tipos: ["fuente", "refugio"] }),
    })
      .then(function (r) { return r.json(); })
      .then(function (json) {
        if (json.ok) {
          TrailMind.mapa.mostrarPois(json.pois);
          if (poiError) poiError.classList.add("oculto");
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

  function limpiar() {
    _bbox = null;
    if (TrailMind.mapa && TrailMind.mapa.limpiarPois) {
      TrailMind.mapa.limpiarPois();
    }
  }

  return {
    establecerBbox: establecerBbox,
    buscar: buscar,
    limpiar: limpiar,
  };

})();
