window.TrailMind = window.TrailMind || {};

window.TrailMind.grafico = (function () {

  var instancia = null;
  var _puntos = null;

  // Plugin inline: dibuja línea vertical (crosshair) en la posición activa del tooltip
  var pluginCrosshair = {
    id: "crosshair",
    afterDraw: function (chart) {
      var activos = chart.tooltip._active;
      if (!activos || activos.length === 0) return;
      var ctx = chart.ctx;
      var x = activos[0].element.x;
      var topY = chart.scales.y.top;
      var bottomY = chart.scales.y.bottom;
      ctx.save();
      ctx.beginPath();
      ctx.moveTo(x, topY);
      ctx.lineTo(x, bottomY);
      ctx.lineWidth = 1.5;
      ctx.strokeStyle = "rgba(45, 106, 79, 0.35)";
      ctx.setLineDash([5, 4]);
      ctx.stroke();
      ctx.restore();
    },
  };

  function dibujar(puntos) {
    _puntos = puntos;

    var elevaciones = puntos.map(function (p) { return p.elevacion_m; });
    var tieneDatos = elevaciones.some(function (e) { return e !== null; });

    var aviso = document.getElementById("grafico-sin-elevacion");
    var canvas = document.getElementById("grafico-elevacion");

    if (!tieneDatos) {
      if (aviso) aviso.style.display = "block";
      if (canvas) canvas.style.display = "none";
      return;
    }

    if (aviso) aviso.style.display = "none";
    if (canvas) canvas.style.display = "block";

    if (instancia) {
      instancia.destroy();
      instancia = null;
    }

    var distancias = _calcularDistanciasAcumuladas(puntos);
    var etiquetas = distancias.map(function (d) { return d.toFixed(1) + " km"; });
    var ctx = canvas.getContext("2d");

    instancia = new Chart(ctx, {
      type: "line",
      plugins: [pluginCrosshair],
      data: {
        labels: etiquetas,
        datasets: [
          {
            label: "Altitud (m)",
            data: elevaciones,
            borderColor: "#2d6a4f",
            backgroundColor: function (context) {
              var chart = context.chart;
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
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: "index",
          intersect: false,
        },
        onHover: function (event, activeElements) {
          if (!_puntos) return;
          if (activeElements.length > 0) {
            var idx = activeElements[0].index;
            var p = _puntos[idx];
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
            titleColor: "rgba(255,255,255,0.7)",
            bodyColor: "#fff",
            padding: 10,
            cornerRadius: 7,
            callbacks: {
              label: function (ctx) {
                var v = ctx.parsed.y;
                return v !== null ? "  " + Math.round(v) + " m" : "  Sin dato";
              },
            },
          },
        },
        scales: {
          x: {
            ticks: {
              maxTicksLimit: 8,
              color: "#8a9490",
              font: { size: 11 },
            },
            grid: { color: "rgba(0,0,0,0.04)" },
          },
          y: {
            ticks: {
              color: "#8a9490",
              font: { size: 11 },
              callback: function (v) { return v + " m"; },
            },
            grid: { color: "rgba(0,0,0,0.06)" },
          },
        },
      },
    });

    // Ocultar marcador al salir del área del gráfico
    canvas.addEventListener("mouseleave", function () {
      if (TrailMind.mapa && TrailMind.mapa.ocultarPuntoCursor) {
        TrailMind.mapa.ocultarPuntoCursor();
      }
    });
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
    var R = 6371;
    var dLat = _rad(b.lat - a.lat);
    var dLon = _rad(b.lon - a.lon);
    var sinLat = Math.sin(dLat / 2);
    var sinLon = Math.sin(dLon / 2);
    var q = sinLat * sinLat + Math.cos(_rad(a.lat)) * Math.cos(_rad(b.lat)) * sinLon * sinLon;
    return R * 2 * Math.atan2(Math.sqrt(q), Math.sqrt(1 - q));
  }

  function _rad(grados) {
    return (grados * Math.PI) / 180;
  }

  return { dibujar: dibujar };

})();
