window.TrailMind = window.TrailMind || {};

window.TrailMind.grafico = (function () {

  var instancia   = null;
  var _puntos     = null;
  var _distancias = null;  // km acumulados por índice
  var _checkpoints = [];   // checkpoints actuales para el plugin
  var _horasCheckpoints = [];  // horas calculadas por itinerario

  // Estado de la selección de tramo
  var _sel = {
    activa:   false,
    arrastrando: false,
    idx0:     null,
    idx1:     null,
    x0:       null,
    x1:       null,
  };

  // ── Plugin crosshair ─────────────────────────────────────────────────────────
  var pluginCrosshair = {
    id: "crosshair",
    afterDraw: function (chart) {
      var activos = chart.tooltip._active;
      if (!activos || activos.length === 0) return;
      var ctx  = chart.ctx;
      var x    = activos[0].element.x;
      var topY = chart.scales.y.top;
      var botY = chart.scales.y.bottom;
      ctx.save();
      ctx.beginPath();
      ctx.moveTo(x, topY);
      ctx.lineTo(x, botY);
      ctx.lineWidth    = 1.5;
      ctx.strokeStyle  = "rgba(45, 106, 79, 0.35)";
      ctx.setLineDash([5, 4]);
      ctx.stroke();
      ctx.restore();
    },
  };

  // ── Plugin checkpoints (líneas verticales) ──────────────────────────────────
  var pluginCheckpoints = {
    id: "checkpoints",
    afterDraw: function (chart) {
      if (!_checkpoints.length || !_puntos) return;
      var ca  = chart.chartArea;
      var ctx = chart.ctx;
      var n   = _puntos.length - 1;

      var colores = { comida: "#f4845f", campamento: "#5390d9", poi: "#9b5de5" };
      var emojis  = { comida: "🍽", campamento: "⛺", poi: "📍" };

      _checkpoints.forEach(function (cp, i) {
        var ratio  = n > 0 ? cp.indice / n : 0;
        var xPos   = ca.left + ratio * (ca.right - ca.left);
        var color  = colores[cp.tipo] || "#888";
        var emoji  = emojis[cp.tipo]  || "📍";
        var hora   = _horasCheckpoints[i] ? _horasCheckpoints[i].llegada : null;

        ctx.save();
        ctx.beginPath();
        ctx.moveTo(xPos, ca.top);
        ctx.lineTo(xPos, ca.bottom);
        ctx.lineWidth   = 1.5;
        ctx.strokeStyle = color;
        ctx.setLineDash([4, 3]);
        ctx.stroke();
        ctx.restore();

        // Etiqueta hora
        if (hora !== null) {
          var h   = Math.floor(((hora % 1440) + 1440) % 1440 / 60);
          var mm  = Math.round(((hora % 1440) + 1440) % 1440 % 60);
          var txt = (h < 10 ? "0" + h : h) + ":" + (mm < 10 ? "0" + mm : mm);
          ctx.save();
          ctx.font         = "bold 9px Inter,sans-serif";
          ctx.fillStyle    = color;
          ctx.textAlign    = "center";
          ctx.fillText(emoji + " " + txt, xPos, ca.top + 10);
          ctx.restore();
        }
      });
    },
  };

  // ── Plugin selección de tramo ────────────────────────────────────────────────
  var pluginSeleccion = {
    id: "seleccion",
    afterDraw: function (chart) {
      if (!_sel.activa || _sel.x0 === null || _sel.x1 === null) return;
      var ca  = chart.chartArea;
      var ctx = chart.ctx;
      var x0  = Math.max(ca.left,  Math.min(_sel.x0, _sel.x1));
      var x1  = Math.min(ca.right, Math.max(_sel.x0, _sel.x1));
      ctx.save();
      ctx.fillStyle = "rgba(244, 132, 95, 0.18)";
      ctx.fillRect(x0, ca.top, x1 - x0, ca.bottom - ca.top);
      ctx.strokeStyle = "rgba(244, 132, 95, 0.7)";
      ctx.lineWidth   = 1;
      ctx.beginPath();
      ctx.moveTo(x0, ca.top); ctx.lineTo(x0, ca.bottom);
      ctx.moveTo(x1, ca.top); ctx.lineTo(x1, ca.bottom);
      ctx.stroke();
      ctx.restore();
    },
  };

  // ── Construcción del chart ───────────────────────────────────────────────────

  function dibujar(puntos) {
    _puntos = puntos;
    _sel    = { activa: false, arrastrando: false, idx0: null, idx1: null, x0: null, x1: null };

    var elevaciones = puntos.map(function (p) { return p.elevacion_m; });
    var tieneDatos  = elevaciones.some(function (e) { return e !== null; });

    var aviso  = document.getElementById("grafico-sin-elevacion");
    var canvas = document.getElementById("grafico-elevacion");

    if (!tieneDatos) {
      if (aviso)  aviso.style.display  = "block";
      if (canvas) canvas.style.display = "none";
      return;
    }

    if (aviso)  aviso.style.display  = "none";
    if (canvas) canvas.style.display = "block";

    if (instancia) {
      instancia.destroy();
      instancia = null;
    }

    _distancias = _calcularDistanciasAcumuladas(puntos);
    var etiquetas = _distancias.map(function (d) { return d.toFixed(1) + " km"; });
    var ctx = canvas.getContext("2d");

    instancia = new Chart(ctx, {
      type: "line",
      plugins: [pluginCrosshair, pluginSeleccion, pluginCheckpoints],
      data: {
        labels: etiquetas,
        datasets: [{
          label: "Altitud (m)",
          data: elevaciones,
          borderColor: "#2d6a4f",
          backgroundColor: function (context) {
            var chart    = context.chart;
            var gradient = chart.ctx.createLinearGradient(0, 0, 0, chart.height);
            gradient.addColorStop(0, "rgba(45, 106, 79, 0.2)");
            gradient.addColorStop(1, "rgba(45, 106, 79, 0.02)");
            return gradient;
          },
          borderWidth: 2,
          pointRadius: 0,
          pointHoverRadius: 4,
          fill: true,
          tension: 0.3,
          spanGaps: true,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        onHover: function (event, activeElements) {
          if (!_puntos) return;
          if (activeElements.length > 0) {
            var idx = activeElements[0].index;
            var p   = _puntos[idx];
            if (p && TrailMind.mapa && TrailMind.mapa.mostrarPuntoCursor) {
              TrailMind.mapa.mostrarPuntoCursor(p.lat, p.lon, p.elevacion_m);
            }
          } else {
            if (TrailMind.mapa && TrailMind.mapa.ocultarPuntoCursor) {
              TrailMind.mapa.ocultarPuntoCursor();
            }
          }
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: "rgba(27, 67, 50, 0.92)",
            titleColor:      "rgba(255,255,255,0.7)",
            bodyColor:       "#fff",
            padding:         10,
            cornerRadius:    7,
            callbacks: {
              label: function (ctx) {
                var alt = ctx.parsed.y;
                var linea = alt !== null ? "  " + Math.round(alt) + " m" : "  Sin dato";
                var perfil = TrailMind.estimacion
                  ? TrailMind.estimacion.obtenerPerfilTiempo()
                  : null;
                if (perfil && perfil.puntos && perfil.puntos[ctx.dataIndex] != null) {
                  var pt  = perfil.puntos[ctx.dataIndex];
                  var min = perfil.modo === "desfavorable"
                    ? pt.tiempo_desfavorable_min
                    : pt.tiempo_optimo_min;
                  linea += "   ⏱ " + _formatearHHMM(min);
                }
                return linea;
              },
            },
          },
        },
        scales: {
          x: {
            ticks: { maxTicksLimit: 8, color: "#8a9490", font: { size: 11 } },
            grid:  { color: "rgba(0,0,0,0.04)" },
          },
          y: {
            ticks: { color: "#8a9490", font: { size: 11 },
                     callback: function (v) { return v + " m"; } },
            grid: { color: "rgba(0,0,0,0.06)" },
          },
        },
      },
    });

    // Ocultar marcador en mapa al salir del gráfico
    canvas.addEventListener("mouseleave", function () {
      if (!_sel.arrastrando) {
        if (TrailMind.mapa && TrailMind.mapa.ocultarPuntoCursor) {
          TrailMind.mapa.ocultarPuntoCursor();
        }
      }
    });

    // ── Selección de tramo por arrastre ────────────────────────────────────────
    canvas.addEventListener("mousedown", function (e) {
      if (!instancia) return;
      var ca = instancia.chartArea;
      var rect = canvas.getBoundingClientRect();
      var xCanvas = e.clientX - rect.left;
      if (xCanvas < ca.left || xCanvas > ca.right) return;
      _sel.arrastrando = true;
      _sel.activa      = false;
      _sel.x0 = xCanvas;
      _sel.x1 = xCanvas;
      _sel.idx0 = _pixelAIndice(xCanvas);
      _sel.idx1 = _sel.idx0;
      _ocultarPanelTramo();
    });

    canvas.addEventListener("mousemove", function (e) {
      if (!_sel.arrastrando || !instancia) return;
      var ca   = instancia.chartArea;
      var rect = canvas.getBoundingClientRect();
      var xCanvas = Math.max(ca.left, Math.min(ca.right, e.clientX - rect.left));
      _sel.x1   = xCanvas;
      _sel.idx1 = _pixelAIndice(xCanvas);
      _sel.activa = true;
      instancia.draw();
    });

    canvas.addEventListener("mouseup", function () {
      if (!_sel.arrastrando) return;
      _sel.arrastrando = false;
      if (!_sel.activa) return;

      var i = Math.min(_sel.idx0, _sel.idx1);
      var j = Math.max(_sel.idx0, _sel.idx1);

      if (j - i < 1) {
        limpiarSeleccion();
        return;
      }

      _mostrarStatsTramo(i, j);
      if (TrailMind.mapa && TrailMind.mapa.resaltarTramo) {
        TrailMind.mapa.resaltarTramo(i, j);
      }
    });

    // Cancelar selección al salir del canvas con botón pulsado
    canvas.addEventListener("mouseleave", function () {
      if (_sel.arrastrando) {
        _sel.arrastrando = false;
        if (!_sel.activa) return;
        var i = Math.min(_sel.idx0, _sel.idx1);
        var j = Math.max(_sel.idx0, _sel.idx1);
        if (j - i >= 1) {
          _mostrarStatsTramo(i, j);
          if (TrailMind.mapa && TrailMind.mapa.resaltarTramo) {
            TrailMind.mapa.resaltarTramo(i, j);
          }
        }
      }
    });
  }

  // ── API pública ──────────────────────────────────────────────────────────────

  function actualizarPerfilTiempo() {
    if (!instancia) return;
    instancia.update("none");
  }

  function marcarPunto(lat, lon) {
    if (!instancia || !_puntos) return;
    var idx = -1;
    for (var i = 0; i < _puntos.length; i++) {
      if (_puntos[i].lat === lat && _puntos[i].lon === lon) {
        idx = i;
        break;
      }
    }
    if (idx === -1) return;
    instancia.tooltip.setActiveElements(
      [{ datasetIndex: 0, index: idx }],
      { x: 0, y: 0 }
    );
    instancia.update("none");
  }

  function limpiarMarcador() {
    if (!instancia) return;
    instancia.tooltip.setActiveElements([], { x: 0, y: 0 });
    instancia.update("none");
  }

  function limpiarSeleccion() {
    _sel = { activa: false, arrastrando: false, idx0: null, idx1: null, x0: null, x1: null };
    if (instancia) instancia.draw();
    _ocultarPanelTramo();
    if (TrailMind.mapa && TrailMind.mapa.limpiarTramoResaltado) {
      TrailMind.mapa.limpiarTramoResaltado();
    }
  }

  function renderCheckpoints(checkpoints, horas) {
    _checkpoints      = checkpoints || [];
    _horasCheckpoints = horas       || [];
    if (instancia) instancia.draw();
  }

  // ── Helpers privados ─────────────────────────────────────────────────────────

  function _pixelAIndice(xCanvas) {
    if (!instancia || !_puntos) return 0;
    var ca    = instancia.chartArea;
    var ratio = (xCanvas - ca.left) / (ca.right - ca.left);
    ratio = Math.max(0, Math.min(1, ratio));
    return Math.round(ratio * (_puntos.length - 1));
  }

  function _mostrarStatsTramo(i, j) {
    var perfil = TrailMind.estimacion
      ? TrailMind.estimacion.obtenerPerfilTiempo()
      : null;

    var distancia = null;
    var desPos = 0, desNeg = 0;
    var tiempoOpt = null, tiempoDes = null;

    if (perfil && perfil.puntos) {
      var pts   = perfil.puntos;
      distancia = pts[j].km_acum - pts[i].km_acum;
      tiempoOpt = pts[j].tiempo_optimo_min - pts[i].tiempo_optimo_min;
      tiempoDes = pts[j].tiempo_desfavorable_min - pts[i].tiempo_desfavorable_min;
      for (var k = i + 1; k <= j; k++) {
        if (pts[k].alt_m != null && pts[k - 1].alt_m != null) {
          var diff = pts[k].alt_m - pts[k - 1].alt_m;
          if (diff > 0) desPos += diff;
          else          desNeg += Math.abs(diff);
        }
      }
    } else if (_distancias) {
      distancia = _distancias[j] - _distancias[i];
      var elevs = _puntos.slice(i, j + 1).map(function (p) { return p.elevacion_m; });
      for (var m = 1; m < elevs.length; m++) {
        if (elevs[m] != null && elevs[m - 1] != null) {
          var d = elevs[m] - elevs[m - 1];
          if (d > 0) desPos += d;
          else       desNeg += Math.abs(d);
        }
      }
    }

    var pendiente = (distancia && distancia > 0)
      ? ((desPos / (distancia * 1000)) * 100).toFixed(1) + " %"
      : "—";

    var el = function (id) { return document.getElementById(id); };
    var distEl = el("tramo-distancia");
    var dpEl   = el("tramo-desnivel-pos");
    var dnEl   = el("tramo-desnivel-neg");
    var pendEl = el("tramo-pendiente");
    var toEl   = el("tramo-tiempo-opt");
    var tdEl   = el("tramo-tiempo-des");
    var panel  = document.getElementById("panel-tramo");
    var btnLimpiar = document.getElementById("btn-limpiar-seleccion");

    if (distEl) distEl.textContent = distancia != null ? distancia.toFixed(2) + " km" : "—";
    if (dpEl)   dpEl.textContent   = "+" + Math.round(desPos) + " m";
    if (dnEl)   dnEl.textContent   = "−" + Math.round(desNeg) + " m";
    if (pendEl) pendEl.textContent = pendiente;
    if (toEl)   toEl.textContent   = tiempoOpt != null ? _formatearHHMM(tiempoOpt) : "—";
    if (tdEl)   tdEl.textContent   = tiempoDes != null ? _formatearHHMM(tiempoDes) : "—";
    if (panel)  panel.classList.remove("oculto");
    if (btnLimpiar) btnLimpiar.classList.remove("oculto");
  }

  function _ocultarPanelTramo() {
    var panel = document.getElementById("panel-tramo");
    if (panel) panel.classList.add("oculto");
    var btn = document.getElementById("btn-limpiar-seleccion");
    if (btn) btn.classList.add("oculto");
  }

  function _formatearHHMM(minutos) {
    var h = Math.floor(minutos / 60);
    var m = Math.round(minutos % 60);
    return h + ":" + (m < 10 ? "0" : "") + m;
  }

  function _calcularDistanciasAcumuladas(puntos) {
    var distancias = [0];
    var acum = 0;
    for (var i = 1; i < puntos.length; i++) {
      acum += _haversineKm(puntos[i - 1], puntos[i]);
      distancias.push(acum);
    }
    return distancias;
  }

  function _haversineKm(a, b) {
    var R    = 6371;
    var dLat = _rad(b.lat - a.lat);
    var dLon = _rad(b.lon - a.lon);
    var sinLat = Math.sin(dLat / 2);
    var sinLon = Math.sin(dLon / 2);
    var q = sinLat * sinLat + Math.cos(_rad(a.lat)) * Math.cos(_rad(b.lat)) * sinLon * sinLon;
    return R * 2 * Math.atan2(Math.sqrt(q), Math.sqrt(1 - q));
  }

  function _rad(grados) { return grados * Math.PI / 180; }

  return {
    dibujar:             dibujar,
    actualizarPerfilTiempo: actualizarPerfilTiempo,
    marcarPunto:         marcarPunto,
    limpiarMarcador:     limpiarMarcador,
    limpiarSeleccion:    limpiarSeleccion,
    renderCheckpoints:   renderCheckpoints,
  };

})();
