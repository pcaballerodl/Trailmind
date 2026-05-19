window.TrailMind = window.TrailMind || {};

window.TrailMind.estadisticas = (function () {

  function mostrar(datos) {
    _setTexto("stat-nombre", datos.nombre_track || "Track sin nombre");
    _setTexto("stat-distancia", _formatearKm(datos.distancia_km));
    _setTexto("stat-desnivel-pos", _formatearM(datos.desnivel_positivo_m));
    _setTexto("stat-desnivel-neg", _formatearM(datos.desnivel_negativo_m));
    _setTexto("stat-alt-max", _formatearM(datos.altitud_max_m));
    _setTexto("stat-alt-min", _formatearM(datos.altitud_min_m));
    _setTexto("stat-alt-media", _formatearM(datos.altitud_media_m));
    _setTexto("stat-puntos", datos.total_puntos.toLocaleString("es"));
    _setTexto("stat-timestamps", datos.tiene_timestamps ? "Sí" : "No");
  }

  function _setTexto(id, valor) {
    var el = document.getElementById(id);
    if (el) el.textContent = valor;
  }

  function _formatearKm(valor) {
    if (valor === null || valor === undefined) return "—";
    return valor.toFixed(2) + " km";
  }

  function _formatearM(valor) {
    if (valor === null || valor === undefined) return "—";
    return Math.round(valor).toLocaleString("es") + " m";
  }

  return { mostrar: mostrar };

})();
