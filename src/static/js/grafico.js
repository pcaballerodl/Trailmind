window.TrailMind = window.TrailMind || {};

window.TrailMind.grafico = (function () {

  var instancia = null;

  function dibujar(puntos) {
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

    // Destruir instancia anterior antes de redibujar
    if (instancia) {
      instancia.destroy();
      instancia = null;
    }

    var distancias = _calcularDistanciasAcumuladas(puntos);

    var etiquetas = distancias.map(function (d) {
      return d.toFixed(1) + " km";
    });

    var ctx = canvas.getContext("2d");

    instancia = new Chart(ctx, {
      type: "line",
      data: {
        labels: etiquetas,
        datasets: [
          {
            label: "Altitud (m)",
            data: elevaciones,
            borderColor: "#2d6a4f",
            backgroundColor: "rgba(45, 106, 79, 0.15)",
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
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function (ctx) {
                var v = ctx.parsed.y;
                return v !== null ? Math.round(v) + " m" : "Sin dato";
              },
            },
          },
        },
        scales: {
          x: {
            ticks: {
              maxTicksLimit: 8,
              color: "#555",
            },
            grid: { color: "rgba(0,0,0,0.05)" },
          },
          y: {
            ticks: {
              color: "#555",
              callback: function (v) { return v + " m"; },
            },
            grid: { color: "rgba(0,0,0,0.08)" },
          },
        },
      },
    });
  }

  // Distancia acumulada aproximada usando haversine simplificado (en km)
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
    var q =
      sinLat * sinLat +
      Math.cos(_rad(a.lat)) * Math.cos(_rad(b.lat)) * sinLon * sinLon;
    return R * 2 * Math.atan2(Math.sqrt(q), Math.sqrt(1 - q));
  }

  function _rad(grados) {
    return (grados * Math.PI) / 180;
  }

  return { dibujar: dibujar };

})();
