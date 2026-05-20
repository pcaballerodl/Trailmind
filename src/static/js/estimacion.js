window.TrailMind = window.TrailMind || {};

window.TrailMind.estimacion = (function () {

  var _resumenTrack = null;

  function establecerTrack(datos) {
    // Solo guardamos el resumen estadístico, nunca el array de puntos
    _resumenTrack = {
      distancia_km:        datos.distancia_km,
      desnivel_positivo_m: datos.desnivel_positivo_m,
      desnivel_negativo_m: datos.desnivel_negativo_m,
      altitud_media_m:     datos.altitud_media_m,
      altitud_max_m:       datos.altitud_max_m,
      tramos_duros_pct:    datos.tramos_duros_pct || null,
    };
  }

  function cargar() {
    if (!_resumenTrack) return;

    var spinner   = document.getElementById("estimacion-spinner");
    var contenido = document.getElementById("estimacion-contenido");

    if (spinner)   spinner.classList.remove("oculto");
    if (contenido) contenido.style.visibility = "hidden";

    var mes = new Date().getMonth() + 1; // 1-12

    fetch("/api/estimacion/tiempo", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ track: _resumenTrack, mes: mes }),
    })
      .then(function (r) { return r.json(); })
      .then(function (json) {
        if (json.ok) {
          _renderizar(json.estimacion);
        }
      })
      .catch(function () { /* estimación auxiliar, error silencioso */ })
      .then(function () {
        if (spinner)   spinner.classList.add("oculto");
        if (contenido) contenido.style.visibility = "visible";
      });
  }

  function _renderizar(estimacion) {
    var elOptimo  = document.getElementById("estimacion-optimo");
    var elDesfav  = document.getElementById("estimacion-desfavorable");
    var elFactores = document.getElementById("estimacion-factores");

    if (elOptimo)  elOptimo.textContent  = _formatearTiempo(estimacion.optimo);
    if (elDesfav)  elDesfav.textContent  = _formatearTiempo(estimacion.desfavorable);

    if (elFactores) {
      var tags = [];
      if (estimacion.factores.factor_altitud > 1.0)         tags.push("🏔 Altitud");
      if (estimacion.factores.factor_nieve > 1.0)           tags.push("❄️ Nieve");
      if (estimacion.factores.con_datos_pendiente)          tags.push("📐 Pendiente");
      elFactores.textContent = tags.length > 0
        ? "Factores: " + tags.join(" · ")
        : "";
    }
  }

  function _formatearTiempo(t) {
    if (t.horas > 0 && t.minutos > 0) return t.horas + " h " + t.minutos + " min";
    if (t.horas > 0)                   return t.horas + " h";
    return t.minutos + " min";
  }

  return {
    establecerTrack: establecerTrack,
    cargar: cargar,
  };

})();
