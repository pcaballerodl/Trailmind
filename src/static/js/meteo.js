window.TrailMind = window.TrailMind || {};

window.TrailMind.meteo = (function () {

  var _lat = null;
  var _lon = null;
  var _previsionActual = null;

  // Iconos por rango de código WMO
  var _ICONOS = [
    { hasta: 2,  icono: "☀️" },
    { hasta: 3,  icono: "⛅" },
    { hasta: 48, icono: "🌫️" },
    { hasta: 67, icono: "🌧️" },
    { hasta: 77, icono: "❄️" },
    { hasta: 82, icono: "🌦️" },
    { hasta: 86, icono: "🌨️" },
    { hasta: 99, icono: "⛈️" },
  ];

  function establecerCoordenadas(lat, lon) {
    _lat = lat;
    _lon = lon;
    // Pre-rellenar fecha con hoy
    var inputFecha = document.getElementById("fecha-expedicion");
    if (inputFecha && !inputFecha.value) {
      inputFecha.value = _fechaHoy();
    }
  }

  function cargar() {
    if (_lat === null || _lon === null) return;

    var inputFecha = document.getElementById("fecha-expedicion");
    var fecha = inputFecha ? inputFecha.value : _fechaHoy();

    if (!fecha) {
      _mostrarErrorMeteo("Selecciona una fecha para la expedición");
      return;
    }

    var dias = 7;
    _mostrarCargando(true);
    _ocultarErrorMeteo();

    fetch("/api/meteo/prevision?lat=" + _lat + "&lon=" + _lon + "&fecha=" + fecha + "&dias=" + dias)
      .then(function (r) { return r.json(); })
      .then(function (json) {
        _mostrarCargando(false);
        if (json.ok) {
          renderizar(json.prevision);
        } else {
          _mostrarErrorMeteo(json.error || "Error al obtener la previsión");
        }
      })
      .catch(function () {
        _mostrarCargando(false);
        _mostrarErrorMeteo("No se pudo conectar con el servidor");
      });
  }

  function renderizar(prevision) {
    _previsionActual = prevision;
    var contenedor = document.getElementById("meteo-tarjetas");
    if (!contenedor) return;

    contenedor.innerHTML = "";

    prevision.dias.forEach(function (dia) {
      var tarjeta = document.createElement("div");
      tarjeta.className = "meteo-tarjeta";

      var nieve = dia.nieve_cm && dia.nieve_cm > 0
        ? '<div class="meteo-nieve">❄️ ' + dia.nieve_cm.toFixed(1) + " cm nieve</div>"
        : "";

      tarjeta.innerHTML =
        '<div class="meteo-fecha">' + _formatearFecha(dia.fecha) + "</div>" +
        '<div class="meteo-icono">' + _iconoPorCodigo(dia.codigo_wmo) + "</div>" +
        '<div class="meteo-desc">' + dia.descripcion + "</div>" +
        '<div class="meteo-temps">' +
          '<span class="meteo-max">' + _val(dia.temp_max_c, "°") + "</span>" +
          '<span class="meteo-min">' + _val(dia.temp_min_c, "°") + "</span>" +
        "</div>" +
        '<div class="meteo-detalle">' +
          '<span title="Precipitación">💧 ' + _val(dia.precipitacion_mm, " mm") + "</span>" +
          '<span title="Viento máximo">💨 ' + _val(dia.viento_max_kmh, " km/h") + "</span>" +
        "</div>" +
        nieve;

      contenedor.appendChild(tarjeta);
    });
  }

  function _iconoPorCodigo(codigo) {
    for (var i = 0; i < _ICONOS.length; i++) {
      if (codigo <= _ICONOS[i].hasta) return _ICONOS[i].icono;
    }
    return "🌡️";
  }

  function _formatearFecha(fechaIso) {
    // "2024-07-15" → "lun 15 jul"
    var partes = fechaIso.split("-");
    var d = new Date(
      parseInt(partes[0]),
      parseInt(partes[1]) - 1,
      parseInt(partes[2])
    );
    return d.toLocaleDateString("es-ES", { weekday: "short", day: "numeric", month: "short" });
  }

  function _val(valor, sufijo) {
    if (valor === null || valor === undefined) return "—";
    return valor.toFixed(1) + sufijo;
  }

  function _fechaHoy() {
    return new Date().toISOString().split("T")[0];
  }

  function _mostrarCargando(visible) {
    var el = document.getElementById("meteo-spinner");
    if (el) el.classList.toggle("oculto", !visible);
    var btn = document.getElementById("btn-consultar-meteo");
    if (btn) btn.disabled = visible;
  }

  function _mostrarErrorMeteo(mensaje) {
    var el = document.getElementById("meteo-error");
    if (el) {
      el.textContent = mensaje;
      el.classList.remove("oculto");
    }
  }

  function _ocultarErrorMeteo() {
    var el = document.getElementById("meteo-error");
    if (el) el.classList.add("oculto");
  }

  function obtenerPrevision() {
    return _previsionActual;
  }

  return {
    establecerCoordenadas: establecerCoordenadas,
    cargar: cargar,
    renderizar: renderizar,
    obtenerPrevision: obtenerPrevision,
  };

})();
