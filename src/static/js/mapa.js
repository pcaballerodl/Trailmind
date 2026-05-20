window.TrailMind = window.TrailMind || {};

window.TrailMind.mapa = (function () {

  var instancia = null;
  var polilinea = null;
  var marcadores = [];
  var _marcadorCursor = null;
  var _marcadoresPoi = [];

  var MAX_PUNTOS_LEAFLET = 2000;

  function inicializar() {
    if (instancia) {
      instancia.remove();
    }
    _marcadorCursor = null;
    _marcadoresPoi = [];
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
    limpiarPois();

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

  function mostrarPuntoCursor(lat, lon) {
    if (!instancia) return;
    if (!_marcadorCursor) {
      _marcadorCursor = L.circleMarker([lat, lon], {
        radius: 7,
        color: "#fff",
        fillColor: "#2d6a4f",
        fillOpacity: 1,
        weight: 2,
        interactive: false,
      }).addTo(instancia);
    } else {
      _marcadorCursor.setLatLng([lat, lon]);
    }
  }

  function ocultarPuntoCursor() {
    if (_marcadorCursor) {
      _marcadorCursor.remove();
      _marcadorCursor = null;
    }
  }

  function mostrarPois(pois) {
    limpiarPois();
    pois.forEach(function (poi) {
      var esFuente = poi.tipo === "fuente";
      var color = esFuente ? "#2980b9" : "#8e44ad";
      var letra = esFuente ? "A" : "R";
      var icono = _crearIcono(color, letra);
      var etiqueta = poi.nombre || (esFuente ? "Fuente de agua" : "Refugio");
      var marcador = L.marker([poi.lat, poi.lon], { icon: icono })
        .bindTooltip(etiqueta)
        .addTo(instancia);
      _marcadoresPoi.push(marcador);
    });
  }

  function limpiarPois() {
    _marcadoresPoi.forEach(function (m) { m.remove(); });
    _marcadoresPoi = [];
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
    mostrarPuntoCursor: mostrarPuntoCursor,
    ocultarPuntoCursor: ocultarPuntoCursor,
    mostrarPois: mostrarPois,
    limpiarPois: limpiarPois,
  };

})();
