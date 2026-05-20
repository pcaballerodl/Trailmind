window.TrailMind = window.TrailMind || {};

window.TrailMind.itinerario = (function () {

  var _checkpoints  = [];
  var _horaSalida   = "08:00";
  var _modo         = "optimo";
  var _dias         = 1;
  var _modoAnadir   = false;   // true cuando el usuario activa añadir checkpoint manual

  // ── API pública ──────────────────────────────────────────────────────────────

  function sugerir(dias) {
    _dias = dias || 1;
    var perfil = TrailMind.estimacion.obtenerPerfilTiempo();
    if (!perfil || !perfil.puntos || perfil.puntos.length < 2) return;

    var pois = (TrailMind.poi && TrailMind.poi.obtenerPois) ? TrailMind.poi.obtenerPois() : [];

    var btnSugerir = document.getElementById("btn-sugerir-checkpoints");
    var spinner    = document.getElementById("itinerario-spinner");
    if (btnSugerir) btnSugerir.disabled = true;
    if (spinner)    spinner.classList.remove("oculto");

    fetch("/api/itinerario/sugerir", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ tramos: perfil.puntos, pois: pois, dias: _dias, modo: _modo }),
    })
      .then(function (r) { return r.json(); })
      .then(function (json) {
        if (!json.ok) return;
        _checkpoints = json.checkpoints;
        _renderTodo();
      })
      .catch(function () {})
      .then(function () {
        if (btnSugerir) btnSugerir.disabled = false;
        if (spinner)    spinner.classList.add("oculto");
      });
  }

  function setHoraSalida(valor) {
    _horaSalida = valor || "08:00";
    _renderTodo();
  }

  function setModo(modo) {
    _modo = modo;
    _renderTodo();
  }

  function limpiar() {
    _checkpoints = [];
    _renderTodo();
  }

  function agregarManual(checkpoint) {
    var cp = {
      id:          checkpoint.tipo + "_m_" + checkpoint.indice + "_" + Date.now(),
      tipo:        checkpoint.tipo,
      indice:      checkpoint.indice,
      km_acum:     checkpoint.km_acum,
      alt_m:       checkpoint.alt_m,
      lat:         checkpoint.lat,
      lon:         checkpoint.lon,
      etiqueta:    checkpoint.etiqueta || _etiquetaPorTipo(checkpoint.tipo),
      duracion_min: checkpoint.duracion_min || _duracionPorTipo(checkpoint.tipo),
      auto:        false,
      poi_cercano: null,
    };
    _checkpoints.push(cp);
    _checkpoints.sort(function (a, b) { return a.indice - b.indice; });
    _renderTodo();
  }

  function eliminar(cpId) {
    _checkpoints = _checkpoints.filter(function (cp) { return cp.id !== cpId; });
    _renderTodo();
  }

  function actualizarDuracion(cpId, minutos) {
    var cp = _checkpoints.find(function (c) { return c.id === cpId; });
    if (cp && minutos >= 0) {
      cp.duracion_min = minutos;
      _renderTodo();
    }
  }

  function abrirModalCheckpoint(lat, lon, indice) {
    var modal = document.getElementById("modal-checkpoint");
    if (!modal) return;
    var perfil = TrailMind.estimacion.obtenerPerfilTiempo();
    var punto  = perfil && perfil.puntos ? perfil.puntos[indice] : null;

    _setVal("modal-cp-lat",    lat !== null ? lat.toFixed(6) : "");
    _setVal("modal-cp-lon",    lon !== null ? lon.toFixed(6) : "");
    _setVal("modal-cp-indice", indice);
    _setVal("modal-cp-km",     punto ? punto.km_acum.toFixed(2) : "");
    _setVal("modal-cp-alt",    punto && punto.alt_m != null ? Math.round(punto.alt_m) : "");
    modal.classList.remove("oculto");
  }

  function setModoAnadir(activo) {
    _modoAnadir = !!activo;
  }

  function getModoAnadir() {
    return _modoAnadir;
  }

  // ── Privada: cálculo de horas ────────────────────────────────────────────────

  function _calcularHoras() {
    var perfil = TrailMind.estimacion.obtenerPerfilTiempo();
    if (!perfil || !_checkpoints.length) return [];

    var campo     = perfil.modo === "desfavorable" ? "tiempo_desfavorable_min" : "tiempo_optimo_min";
    var baseMins  = _horaSalidaEnMinutos();
    var pausas    = 0;

    return _checkpoints.map(function (cp) {
      var viaje   = (perfil.puntos[cp.indice] || {})[campo] || 0;
      var llegada = baseMins + viaje + pausas;
      var salida  = llegada + cp.duracion_min;
      pausas     += cp.duracion_min;
      return { cp: cp, llegada: llegada, salida: salida };
    });
  }

  function _horaSalidaEnMinutos() {
    var partes = (_horaSalida || "08:00").split(":");
    return parseInt(partes[0], 10) * 60 + (parseInt(partes[1], 10) || 0);
  }

  function _formatearHora(minutos) {
    var dias_extra = Math.floor(minutos / 1440);
    var m = ((minutos % 1440) + 1440) % 1440;
    var h = Math.floor(m / 60);
    var mm = Math.round(m % 60);
    var sufijo = dias_extra > 0 ? " +" + dias_extra + "d" : "";
    return _pad2(h) + ":" + _pad2(mm) + sufijo;
  }

  function _pad2(n) { return n < 10 ? "0" + n : String(n); }

  function _formatMin(min) {
    if (min <= 0) return "0 min";
    var h = Math.floor(Math.abs(min) / 60);
    var m = Math.round(Math.abs(min) % 60);
    if (h === 0) return m + " min";
    return h + "h" + (m > 0 ? _pad2(m) : "");
  }

  function _iconoTipo(tipo) {
    return { comida: "🍽️", campamento: "⛺", poi: "📍" }[tipo] || "📍";
  }

  function _etiquetaPorTipo(tipo) {
    return { comida: "Parada comida", campamento: "Campamento", poi: "Punto de interés" }[tipo] || "Checkpoint";
  }

  function _duracionPorTipo(tipo) {
    return { comida: 45, campamento: 480, poi: 15 }[tipo] || 15;
  }

  // ── Privada: render ──────────────────────────────────────────────────────────

  function _renderTodo() {
    var horas = _calcularHoras();
    _renderPanel(horas);
    if (TrailMind.grafico && TrailMind.grafico.renderCheckpoints) {
      TrailMind.grafico.renderCheckpoints(_checkpoints, horas);
    }
    if (TrailMind.mapa && TrailMind.mapa.renderCheckpoints) {
      TrailMind.mapa.renderCheckpoints(_checkpoints, horas);
    }
  }

  function _renderPanel(horas) {
    var timeline = document.getElementById("itinerario-timeline");
    if (!timeline) return;

    if (!_checkpoints.length) {
      timeline.innerHTML =
        '<p class="it-vacio">Sin checkpoints. Usa "Sugerir" o añade puntos manualmente en el mapa.</p>';
      return;
    }

    var perfil   = TrailMind.estimacion.obtenerPerfilTiempo();
    var campo    = perfil && perfil.modo === "desfavorable" ? "tiempo_desfavorable_min" : "tiempo_optimo_min";
    var baseMins = _horaSalidaEnMinutos();

    var html        = "";
    var prev_indice = 0;
    var prev_km     = 0;
    var prev_salida = baseMins;

    horas.forEach(function (item, k) {
      var cp = item.cp;

      // Tramo previo al checkpoint
      var km_tramo      = cp.km_acum - prev_km;
      var duracion_tramo = item.llegada - prev_salida;
      var des           = _desnivelTramo(perfil, prev_indice, cp.indice);

      html += '<div class="it-tramo">' +
        '<span class="it-tramo-km">' + km_tramo.toFixed(1) + ' km</span>' +
        '<span class="it-tramo-des">' +
          '<span class="verde">+' + des.pos + ' m</span> ' +
          '<span class="rojo">−' + des.neg + ' m</span>' +
        '</span>' +
        '<span class="it-tramo-tiempo">' + _formatMin(duracion_tramo) + '</span>' +
      '</div>';

      // Checkpoint
      html += '<div class="it-checkpoint" data-id="' + cp.id + '">' +
        '<span class="it-cp-icono">' + _iconoTipo(cp.tipo) + '</span>' +
        '<div class="it-cp-info">' +
          '<span class="it-cp-etiqueta">' + _escHtml(cp.etiqueta) + '</span>' +
          (cp.poi_cercano
            ? '<span class="it-cp-poi">📌 ' +
                _escHtml(cp.poi_cercano.nombre || cp.poi_cercano.tipo) +
                ' (' + cp.poi_cercano.distancia_m + ' m)</span>'
            : '') +
          '<span class="it-cp-horas">' +
            '↓ ' + _formatearHora(item.llegada) + ' · ' +
            '<span class="it-cp-duracion" contenteditable="true" ' +
              'data-id="' + cp.id + '">' + cp.duracion_min + '</span> min' +
            ' · ↑ ' + _formatearHora(item.salida) +
          '</span>' +
        '</div>' +
        '<button class="it-cp-borrar" data-id="' + cp.id + '" title="Eliminar">✕</button>' +
      '</div>';

      prev_indice = cp.indice;
      prev_km     = cp.km_acum;
      prev_salida = item.salida;
    });

    // Tramo final hasta el fin del track
    if (perfil && perfil.puntos && perfil.puntos.length > 0) {
      var idx_fin     = perfil.puntos.length - 1;
      var t_fin_viaje = (perfil.puntos[idx_fin] || {})[campo] || 0;
      var suma_pausas = horas.reduce(function (acc, it) { return acc + it.cp.duracion_min; }, 0);
      var fin_llegada = baseMins + t_fin_viaje + suma_pausas;
      var km_fin      = (perfil.puntos[idx_fin] || {}).km_acum || 0;
      var des_fin     = _desnivelTramo(perfil, prev_indice, idx_fin);

      html += '<div class="it-tramo">' +
        '<span class="it-tramo-km">' + (km_fin - prev_km).toFixed(1) + ' km</span>' +
        '<span class="it-tramo-des">' +
          '<span class="verde">+' + des_fin.pos + ' m</span> ' +
          '<span class="rojo">−' + des_fin.neg + ' m</span>' +
        '</span>' +
        '<span class="it-tramo-tiempo">' + _formatMin(fin_llegada - prev_salida) + '</span>' +
      '</div>';

      html += '<div class="it-checkpoint it-checkpoint--fin">' +
        '<span class="it-cp-icono">🏁</span>' +
        '<div class="it-cp-info">' +
          '<span class="it-cp-etiqueta">Llegada al final</span>' +
          '<span class="it-cp-horas">↓ ' + _formatearHora(fin_llegada) + '</span>' +
        '</div>' +
      '</div>';
    }

    timeline.innerHTML = html;

    // Eventos: borrar
    timeline.querySelectorAll(".it-cp-borrar").forEach(function (btn) {
      btn.addEventListener("click", function () { eliminar(this.dataset.id); });
    });

    // Eventos: editar duración
    timeline.querySelectorAll(".it-cp-duracion").forEach(function (span) {
      span.addEventListener("blur", function () {
        var min = parseInt(this.textContent, 10);
        if (!isNaN(min) && min >= 0) actualizarDuracion(this.dataset.id, min);
      });
      span.addEventListener("keydown", function (e) {
        if (e.key === "Enter") { e.preventDefault(); this.blur(); }
      });
    });
  }

  function _desnivelTramo(perfil, idx_ini, idx_fin) {
    if (!perfil || !perfil.puntos) return { pos: 0, neg: 0 };
    var pos = 0; var neg = 0;
    for (var i = idx_ini + 1; i <= idx_fin && i < perfil.puntos.length; i++) {
      var a = perfil.puntos[i - 1].alt_m;
      var b = perfil.puntos[i].alt_m;
      if (a != null && b != null) {
        var d = b - a;
        if (d > 0) pos += d; else neg -= d;
      }
    }
    return { pos: Math.round(pos), neg: Math.round(neg) };
  }

  function _escHtml(str) {
    if (!str) return "";
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function _setVal(id, val) {
    var el = document.getElementById(id);
    if (el) el.value = val;
  }

  return {
    sugerir:             sugerir,
    setHoraSalida:       setHoraSalida,
    setModo:             setModo,
    limpiar:             limpiar,
    agregarManual:       agregarManual,
    eliminar:            eliminar,
    actualizarDuracion:  actualizarDuracion,
    abrirModalCheckpoint: abrirModalCheckpoint,
    setModoAnadir:       setModoAnadir,
    getModoAnadir:       getModoAnadir,
  };

})();
