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

    if (polilinea) {
      polilinea.remove();
      polilinea = null;
    }
    marcadores.forEach(function (m) { m.remove(); });
    marcadores = [];
    limpiarPois();

    var puntosParaLeaflet = _muestrear(puntos);
    var coordenadas = puntosParaLeaflet.map(function (p) { return [p.lat, p.lon]; });

    if (coordenadas.length === 0) return;

    polilinea = L.polyline(coordenadas, {
      color: "#2d6a4f",
      weight: 3.5,
      opacity: 0.85,
    }).addTo(instancia);

    var iconoInicio = _crearIconoLetra("#2d6a4f", "S");
    var iconoFin = _crearIconoLetra("#c0392b", "F");

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
        weight: 2.5,
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
      var emoji = esFuente ? "💧" : "⛺";
      var tipoLabel = esFuente ? "Fuente de agua" : "Refugio";
      var nombre = poi.nombre || tipoLabel;
      var coordsTexto = poi.lat.toFixed(5) + ", " + poi.lon.toFixed(5);

      var contenidoPopup =
        '<div class="poi-popup">' +
        '<div class="poi-popup-tipo">' + emoji + " " + tipoLabel + "</div>" +
        '<div class="poi-popup-nombre">' + nombre + "</div>" +
        '<div class="poi-popup-coords">📍 ' + coordsTexto + "</div>" +
        '<button class="poi-popup-copiar" data-coords="' + coordsTexto + '">Copiar coordenadas</button>' +
        "</div>";

      var icono = _crearIconoEmoji(emoji);
      var marcador = L.marker([poi.lat, poi.lon], { icon: icono }).bindPopup(contenidoPopup);

      marcador.on("popupopen", function () {
        var popup = marcador.getPopup();
        if (!popup) return;
        var contenedor = popup.getElement();
        if (!contenedor) return;
        var btn = contenedor.querySelector(".poi-popup-copiar");
        if (!btn) return;
        var coords = btn.getAttribute("data-coords");
        btn.addEventListener("click", function () {
          _copiarTexto(coords, btn);
        });
      });

      marcador.addTo(instancia);
      _marcadoresPoi.push(marcador);
    });
  }

  function limpiarPois() {
    _marcadoresPoi.forEach(function (m) { m.remove(); });
    _marcadoresPoi = [];
  }

  function _copiarTexto(texto, btnRef) {
    var exito = function () {
      if (!btnRef) return;
      btnRef.textContent = "✓ Copiado";
      setTimeout(function () { btnRef.textContent = "Copiar coordenadas"; }, 1500);
    };
    if (navigator.clipboard) {
      navigator.clipboard.writeText(texto).then(exito).catch(function () {
        _copiarFallback(texto, btnRef, exito);
      });
    } else {
      _copiarFallback(texto, btnRef, exito);
    }
  }

  function _copiarFallback(texto, btnRef, exito) {
    var ta = document.createElement("textarea");
    ta.value = texto;
    ta.style.cssText = "position:fixed;top:0;left:0;opacity:0";
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    try { document.execCommand("copy"); exito(); } catch (e) {}
    document.body.removeChild(ta);
  }

  function _muestrear(puntos) {
    if (puntos.length <= MAX_PUNTOS_LEAFLET) return puntos;
    var paso = Math.ceil(puntos.length / MAX_PUNTOS_LEAFLET);
    var muestra = [];
    for (var i = 0; i < puntos.length; i += paso) {
      muestra.push(puntos[i]);
    }
    if (muestra[muestra.length - 1] !== puntos[puntos.length - 1]) {
      muestra.push(puntos[puntos.length - 1]);
    }
    return muestra;
  }

  // Icono circular con letra para inicio/fin
  function _crearIconoLetra(color, letra) {
    return L.divIcon({
      className: "",
      html:
        '<div style="background:' + color + ';color:#fff;width:24px;height:24px;border-radius:50%;' +
        'display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;' +
        'border:2.5px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,.3);font-family:Inter,system-ui,sans-serif">' +
        letra + "</div>",
      iconSize: [24, 24],
      iconAnchor: [12, 12],
    });
  }

  // Icono con emoji para POIs
  function _crearIconoEmoji(emoji) {
    return L.divIcon({
      className: "",
      html:
        '<div style="width:34px;height:34px;display:flex;align-items:center;justify-content:center;' +
        'font-size:19px;background:#fff;border-radius:50%;' +
        'box-shadow:0 2px 10px rgba(0,0,0,0.22);border:2px solid rgba(255,255,255,0.9)">' +
        emoji + "</div>",
      iconSize: [34, 34],
      iconAnchor: [17, 17],
      popupAnchor: [0, -20],
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
