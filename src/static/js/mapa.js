window.TrailMind = window.TrailMind || {};

window.TrailMind.mapa = (function () {

  var instancia = null;
  var polilinea = null;
  var marcadores = [];

  var MAX_PUNTOS_LEAFLET = 2000;

  function inicializar() {
    if (instancia) {
      instancia.remove();
    }
    instancia = L.map("mapa").setView([40.4, -3.7], 6);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "© OpenStreetMap contributors",
      maxZoom: 18,
    }).addTo(instancia);
  }

  function dibujar(puntos) {
    if (!instancia) return;

    // Limpiar elementos anteriores
    if (polilinea) {
      polilinea.remove();
      polilinea = null;
    }
    marcadores.forEach(function (m) { m.remove(); });
    marcadores = [];

    var puntosParaLeaflet = _muestrear(puntos);
    var coordenadas = puntosParaLeaflet.map(function (p) {
      return [p.lat, p.lon];
    });

    if (coordenadas.length === 0) return;

    polilinea = L.polyline(coordenadas, {
      color: "#2d6a4f",
      weight: 3,
      opacity: 0.85,
    }).addTo(instancia);

    // Marcador de inicio y fin sobre los puntos originales (no muestreados)
    var iconoInicio = _crearIcono("#2d6a4f", "S");
    var iconoFin = _crearIcono("#c0392b", "F");

    var inicio = L.marker([puntos[0].lat, puntos[0].lon], { icon: iconoInicio })
      .bindTooltip("Inicio")
      .addTo(instancia);
    var fin = L.marker(
      [puntos[puntos.length - 1].lat, puntos[puntos.length - 1].lon],
      { icon: iconoFin }
    )
      .bindTooltip("Fin")
      .addTo(instancia);

    marcadores.push(inicio, fin);
    instancia.fitBounds(polilinea.getBounds(), { padding: [30, 30] });
  }

  // Devuelve un subconjunto uniforme si el track es muy denso
  function _muestrear(puntos) {
    if (puntos.length <= MAX_PUNTOS_LEAFLET) return puntos;
    var paso = Math.ceil(puntos.length / MAX_PUNTOS_LEAFLET);
    var muestra = [];
    for (var i = 0; i < puntos.length; i += paso) {
      muestra.push(puntos[i]);
    }
    // Garantizar que el último punto siempre está incluido
    if (muestra[muestra.length - 1] !== puntos[puntos.length - 1]) {
      muestra.push(puntos[puntos.length - 1]);
    }
    return muestra;
  }

  function _crearIcono(color, letra) {
    return L.divIcon({
      className: "",
      html:
        '<div style="background:' +
        color +
        ';color:#fff;width:22px;height:22px;border-radius:50%;' +
        'display:flex;align-items:center;justify-content:center;' +
        'font-size:11px;font-weight:700;border:2px solid #fff;' +
        'box-shadow:0 1px 4px rgba(0,0,0,.4)">' +
        letra +
        "</div>",
      iconSize: [22, 22],
      iconAnchor: [11, 11],
    });
  }

  return {
    inicializar: inicializar,
    dibujar: dibujar,
  };

})();
