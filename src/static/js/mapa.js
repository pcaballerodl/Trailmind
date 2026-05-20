window.TrailMind = window.TrailMind || {};

window.TrailMind.mapa = (function () {

  var instancia          = null;
  var polilinea          = null;
  var _polylineGhost     = null;   // polilínea invisible para captura de hover
  var _polylineTramo     = null;   // polilínea resaltada del tramo seleccionado
  var marcadores         = [];
  var _marcadorCursor    = null;
  var _marcadoresPoi     = [];
  var _marcadoresCheckp  = [];     // marcadores de checkpoints
  var _segmentosGradiente = [];
  var _modoGradiente     = false;
  var _modoAnadirCheckp  = false;  // cursor modo añadir checkpoint
  var _controlLeyenda    = null;
  var _puntosActuales    = null;   // array completo (sin subsampling)
  var _puntosSubmuestra  = null;   // array subsampled usado en Leaflet

  var MAX_PUNTOS_LEAFLET = 2000;
  var CLAVE_CAPA = "trailmind_capa_activa";

  // ── Inicialización ───────────────────────────────────────────────────────────

  function inicializar() {
    if (instancia) {
      instancia.remove();
    }
    _marcadorCursor    = null;
    _marcadoresPoi     = [];
    _marcadoresCheckp  = [];
    _segmentosGradiente = [];
    _modoGradiente     = false;
    _modoAnadirCheckp  = false;
    _controlLeyenda    = null;
    _puntosActuales    = null;
    _puntosSubmuestra  = null;
    _polylineGhost     = null;
    _polylineTramo     = null;

    instancia = L.map("mapa").setView([40.4, -3.7], 6);

    var capaOSM = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "© OpenStreetMap contributors",
      maxZoom: 18,
    });
    var capaTopoMap = L.tileLayer("https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png", {
      attribution: "© OpenTopoMap contributors",
      maxZoom: 17,
    });
    var capaCartoDB = L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
      attribution: "© CartoDB",
      maxZoom: 19,
    });
    var capaESRI = L.tileLayer(
      "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
      { attribution: "© Esri", maxZoom: 18 }
    );
    var capaIGN = L.tileLayer(
      "https://www.ign.es/wmts/mapa-raster?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0" +
      "&LAYER=MTN&STYLE=default&TILEMATRIXSET=GoogleMapsCompatible" +
      "&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/jpeg",
      { attribution: "© IGN España", maxZoom: 17 }
    );
    var overlayWaymarked = L.tileLayer("https://tile.waymarkedtrails.org/hiking/{z}/{x}/{y}.png", {
      attribution: "© Waymarked Trails",
      maxZoom: 19,
      opacity: 0.7,
    });

    var capasBase = {
      "OpenStreetMap": capaOSM,
      "OpenTopoMap":   capaTopoMap,
      "CartoDB Oscuro": capaCartoDB,
      "ESRI Satélite": capaESRI,
      "IGN España":    capaIGN,
    };
    var overlays = { "Senderos (Waymarked)": overlayWaymarked };

    var capaNombre = localStorage.getItem(CLAVE_CAPA) || "OpenStreetMap";
    var capaActiva = capasBase[capaNombre] || capaOSM;
    capaActiva.addTo(instancia);

    L.control.layers(capasBase, overlays, { position: "topright" }).addTo(instancia);

    instancia.on("baselayerchange", function (e) {
      localStorage.setItem(CLAVE_CAPA, e.name);
    });
  }

  // ── Dibujo del track ─────────────────────────────────────────────────────────

  function dibujar(puntos) {
    if (!instancia) return;

    limpiarTramoResaltado();

    _segmentosGradiente.forEach(function (s) { s.remove(); });
    _segmentosGradiente = [];
    _modoGradiente      = false;
    if (_controlLeyenda) { _controlLeyenda.remove(); _controlLeyenda = null; }

    if (polilinea)       { polilinea.remove();      polilinea      = null; }
    if (_polylineGhost)  { _polylineGhost.remove(); _polylineGhost = null; }
    marcadores.forEach(function (m) { m.remove(); });
    marcadores = [];
    limpiarPois();

    _puntosActuales   = puntos;
    _puntosSubmuestra = _muestrear(puntos);
    var coordenadas   = _puntosSubmuestra.map(function (p) { return [p.lat, p.lon]; });

    if (coordenadas.length === 0) return;

    polilinea = L.polyline(coordenadas, {
      color: "#2d6a4f", weight: 3.5, opacity: 0.85,
    }).addTo(instancia);

    // Ghost polyline invisible (ancha) para capturar eventos de hover
    _polylineGhost = L.polyline(coordenadas, {
      weight: 20, opacity: 0, interactive: true,
    }).addTo(instancia);

    _polylineGhost.on("mousemove", _onGhostMousemove);
    _polylineGhost.on("mouseout",  _onGhostMouseout);

    var iconoInicio = _crearIconoLetra("#2d6a4f", "S");
    var iconoFin    = _crearIconoLetra("#c0392b", "F");

    var inicio = L.marker([puntos[0].lat, puntos[0].lon], { icon: iconoInicio })
      .bindTooltip("Inicio").addTo(instancia);
    var fin = L.marker(
      [puntos[puntos.length - 1].lat, puntos[puntos.length - 1].lon],
      { icon: iconoFin }
    ).bindTooltip("Fin").addTo(instancia);

    marcadores.push(inicio, fin);
    instancia.fitBounds(polilinea.getBounds(), { padding: [30, 30] });
  }

  // ── Hover mapa → gráfico ─────────────────────────────────────────────────────

  function _onGhostMousemove(e) {
    if (!_puntosSubmuestra || !instancia) return;

    var idx = _encontrarIndiceMasCercano(e.latlng.lat, e.latlng.lng);
    var p   = _puntosSubmuestra[idx];
    if (!p) return;

    // Verificar proximidad en píxeles (umbral 15px)
    var pxPunto  = instancia.latLngToContainerPoint([p.lat, p.lon]);
    var pxCursor = instancia.latLngToContainerPoint(e.latlng);
    var dist = Math.hypot(pxPunto.x - pxCursor.x, pxPunto.y - pxCursor.y);
    if (dist > 15) return;

    if (TrailMind.grafico && TrailMind.grafico.marcarPunto) {
      TrailMind.grafico.marcarPunto(p.lat, p.lon);
    }
  }

  function _onGhostMouseout() {
    if (TrailMind.grafico && TrailMind.grafico.limpiarMarcador) {
      TrailMind.grafico.limpiarMarcador();
    }
  }

  function _encontrarIndiceMasCercano(lat, lon) {
    var minDist = Infinity;
    var minIdx  = 0;
    for (var i = 0; i < _puntosSubmuestra.length; i++) {
      var p = _puntosSubmuestra[i];
      var d = (p.lat - lat) * (p.lat - lat) + (p.lon - lon) * (p.lon - lon);
      if (d < minDist) { minDist = d; minIdx = i; }
    }
    return minIdx;
  }

  // ── Resaltado de tramo seleccionado ─────────────────────────────────────────

  function resaltarTramo(iInicio, iFin) {
    limpiarTramoResaltado();
    if (!instancia || !_puntosActuales) return;

    var slice = _puntosActuales.slice(iInicio, iFin + 1);
    // Subsampling del tramo si es muy largo
    var muestra = slice.length > 2000 ? _muestrear(slice) : slice;
    var coords  = muestra.map(function (p) { return [p.lat, p.lon]; });

    _polylineTramo = L.polyline(coords, {
      color: "#f4845f", weight: 6, opacity: 0.9,
    }).addTo(instancia);
  }

  function limpiarTramoResaltado() {
    if (_polylineTramo) {
      _polylineTramo.remove();
      _polylineTramo = null;
    }
  }

  function renderCheckpoints(checkpoints) {
    // Limpiar marcadores anteriores
    _marcadoresCheckp.forEach(function (m) { m.remove(); });
    _marcadoresCheckp = [];

    if (!instancia || !checkpoints || !checkpoints.length) return;

    checkpoints.forEach(function (cp) {
      if (cp.lat == null || cp.lon == null) return;
      var icono   = _crearIconoCheckpoint(cp.tipo);
      var popup   = _contenidoPopupCheckpoint(cp);
      var marcador = L.marker([cp.lat, cp.lon], { icon: icono, zIndexOffset: 500 })
        .bindPopup(popup)
        .addTo(instancia);
      _marcadoresCheckp.push(marcador);
    });
  }

  function activarModoCheckpoint() {
    _modoAnadirCheckp = true;
    if (instancia) {
      L.DomUtil.addClass(instancia.getContainer(), "cursor-crosshair");
      instancia.on("click", _onMapClickCheckpoint);
    }
  }

  function desactivarModoCheckpoint() {
    _modoAnadirCheckp = false;
    if (instancia) {
      L.DomUtil.removeClass(instancia.getContainer(), "cursor-crosshair");
      instancia.off("click", _onMapClickCheckpoint);
    }
  }

  function _onMapClickCheckpoint(e) {
    if (!_modoAnadirCheckp || !_puntosActuales) return;
    var lat = e.latlng.lat;
    var lon = e.latlng.lng;

    // Encontrar el punto del track más cercano al click
    var idx = _encontrarIndiceMasCercanoLngLat(lat, lon, _puntosActuales);

    if (TrailMind.itinerario && TrailMind.itinerario.abrirModalCheckpoint) {
      TrailMind.itinerario.abrirModalCheckpoint(lat, lon, idx);
    }
  }

  function _encontrarIndiceMasCercanoLngLat(lat, lon, puntos) {
    var minDist = Infinity;
    var minIdx  = 0;
    for (var i = 0; i < puntos.length; i++) {
      var p = puntos[i];
      var d = (p.lat - lat) * (p.lat - lat) + (p.lon - lon) * (p.lon - lon);
      if (d < minDist) { minDist = d; minIdx = i; }
    }
    return minIdx;
  }

  function _crearIconoCheckpoint(tipo) {
    var emojis = { comida: "🍽️", campamento: "⛺", poi: "📍" };
    var colores = { comida: "#f4845f", campamento: "#5390d9", poi: "#9b5de5" };
    var emoji = emojis[tipo]  || "📍";
    var color = colores[tipo] || "#888";
    return L.divIcon({
      className: "",
      html: '<div style="width:34px;height:34px;display:flex;align-items:center;justify-content:center;' +
            'font-size:17px;background:' + color + ';border-radius:50%;' +
            'box-shadow:0 2px 10px rgba(0,0,0,0.3);border:2.5px solid #fff">' +
            emoji + "</div>",
      iconSize: [34, 34], iconAnchor: [17, 17], popupAnchor: [0, -20],
    });
  }

  function _contenidoPopupCheckpoint(cp) {
    return '<div class="poi-popup">' +
      '<div class="poi-popup-tipo">' + (cp.etiqueta || cp.tipo) + '</div>' +
      '<div class="poi-popup-nombre">' +
        'km ' + (cp.km_acum || 0).toFixed(1) +
        (cp.alt_m ? ' · ' + Math.round(cp.alt_m) + ' m' : '') +
      '</div>' +
      (cp.poi_cercano
        ? '<div class="poi-popup-coords">📌 ' + (cp.poi_cercano.nombre || cp.poi_cercano.tipo) +
          ' (' + cp.poi_cercano.distancia_m + ' m)</div>'
        : '') +
    '</div>';
  }

  // ── Cursor hover gráfico → mapa ──────────────────────────────────────────────

  function mostrarPuntoCursor(lat, lon) {
    if (!instancia) return;
    if (!_marcadorCursor) {
      _marcadorCursor = L.circleMarker([lat, lon], {
        radius: 7, color: "#fff", fillColor: "#2d6a4f",
        fillOpacity: 1, weight: 2.5, interactive: false,
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

  // ── Gradiente de pendiente ───────────────────────────────────────────────────

  function toggleGradiente() {
    if (!instancia || !_puntosActuales) return;
    _modoGradiente = !_modoGradiente;

    if (_modoGradiente) {
      if (polilinea) polilinea.setStyle({ opacity: 0 });
      if (_segmentosGradiente.length === 0) {
        _segmentosGradiente = _calcularSegmentosGradiente(_puntosSubmuestra);
      }
      _segmentosGradiente.forEach(function (s) { s.addTo(instancia); });
      _controlLeyenda = _crearControlLeyenda();
      _controlLeyenda.addTo(instancia);
    } else {
      if (polilinea) polilinea.setStyle({ opacity: 0.85 });
      _segmentosGradiente.forEach(function (s) { s.remove(); });
      if (_controlLeyenda) { _controlLeyenda.remove(); _controlLeyenda = null; }
    }
  }

  function invalidarTamano() {
    if (instancia) instancia.invalidateSize();
  }

  // ── POIs ─────────────────────────────────────────────────────────────────────

  function mostrarPois(pois) {
    limpiarPois();
    pois.forEach(function (poi) {
      var esFuente = poi.tipo === "fuente";
      var emoji    = esFuente ? "💧" : "⛺";
      var tipoLabel = esFuente ? "Fuente de agua" : "Refugio";
      var nombre   = poi.nombre || tipoLabel;
      var coordsTexto = poi.lat.toFixed(5) + ", " + poi.lon.toFixed(5);

      var contenidoPopup =
        '<div class="poi-popup">' +
        '<div class="poi-popup-tipo">' + emoji + " " + tipoLabel + "</div>" +
        '<div class="poi-popup-nombre">' + nombre + "</div>" +
        '<div class="poi-popup-coords">📍 ' + coordsTexto + "</div>" +
        '<button class="poi-popup-copiar" data-coords="' + coordsTexto + '">Copiar coordenadas</button>' +
        "</div>";

      var icono   = _crearIconoEmoji(emoji);
      var marcador = L.marker([poi.lat, poi.lon], { icon: icono }).bindPopup(contenidoPopup);

      marcador.on("popupopen", function () {
        var popup     = marcador.getPopup();
        var contenedor = popup && popup.getElement();
        var btn = contenedor && contenedor.querySelector(".poi-popup-copiar");
        if (!btn) return;
        btn.addEventListener("click", function () {
          _copiarTexto(btn.getAttribute("data-coords"), btn);
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

  // ── Helpers privados ─────────────────────────────────────────────────────────

  function _calcularSegmentosGradiente(puntos) {
    var resultado   = [];
    if (!puntos || puntos.length < 2) return resultado;
    var segActual   = [puntos[0]];
    var colorActual = _colorPendiente(0);

    for (var i = 1; i < puntos.length; i++) {
      var p1 = puntos[i - 1];
      var p2 = puntos[i];
      var distH = _haversineMetros(p1, p2);
      var pendiente = 0;
      if (distH > 0.1 && p1.elevacion_m != null && p2.elevacion_m != null) {
        pendiente = Math.abs(p2.elevacion_m - p1.elevacion_m) / distH * 100;
      }
      var color = _colorPendiente(pendiente);
      if (color !== colorActual) {
        if (segActual.length >= 2) {
          resultado.push(L.polyline(
            segActual.map(function (p) { return [p.lat, p.lon]; }),
            { color: colorActual, weight: 4, opacity: 0.95 }
          ));
        }
        segActual   = [p1, p2];
        colorActual = color;
      } else {
        segActual.push(p2);
      }
    }
    if (segActual.length >= 2) {
      resultado.push(L.polyline(
        segActual.map(function (p) { return [p.lat, p.lon]; }),
        { color: colorActual, weight: 4, opacity: 0.95 }
      ));
    }
    return resultado;
  }

  function _colorPendiente(pct) {
    if (pct < 5)  return "#52b788";
    if (pct < 15) return "#f9c74f";
    if (pct < 25) return "#f4845f";
    return "#e63946";
  }

  function _haversineMetros(a, b) {
    var R    = 6371000;
    var dLat = (b.lat - a.lat) * Math.PI / 180;
    var dLon = (b.lon - a.lon) * Math.PI / 180;
    var lat1 = a.lat * Math.PI / 180;
    var lat2 = b.lat * Math.PI / 180;
    var x = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.sin(dLon / 2) * Math.sin(dLon / 2) * Math.cos(lat1) * Math.cos(lat2);
    return R * 2 * Math.atan2(Math.sqrt(x), Math.sqrt(1 - x));
  }

  function _crearControlLeyenda() {
    var leyenda = L.control({ position: "bottomright" });
    leyenda.onAdd = function () {
      var div = L.DomUtil.create("div", "leyenda-gradiente");
      div.innerHTML =
        '<div class="leyenda-titulo">Pendiente</div>' +
        '<div class="leyenda-item"><span class="leyenda-color" style="background:#52b788"></span>&lt;5%</div>' +
        '<div class="leyenda-item"><span class="leyenda-color" style="background:#f9c74f"></span>5–15%</div>' +
        '<div class="leyenda-item"><span class="leyenda-color" style="background:#f4845f"></span>15–25%</div>' +
        '<div class="leyenda-item"><span class="leyenda-color" style="background:#e63946"></span>&gt;25%</div>';
      return div;
    };
    return leyenda;
  }

  function _muestrear(puntos) {
    if (puntos.length <= MAX_PUNTOS_LEAFLET) return puntos;
    var paso   = Math.ceil(puntos.length / MAX_PUNTOS_LEAFLET);
    var muestra = [];
    for (var i = 0; i < puntos.length; i += paso) {
      muestra.push(puntos[i]);
    }
    if (muestra[muestra.length - 1] !== puntos[puntos.length - 1]) {
      muestra.push(puntos[puntos.length - 1]);
    }
    return muestra;
  }

  function _crearIconoLetra(color, letra) {
    return L.divIcon({
      className: "",
      html: '<div style="background:' + color + ';color:#fff;width:24px;height:24px;border-radius:50%;' +
            'display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;' +
            'border:2.5px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,.3);font-family:Inter,system-ui,sans-serif">' +
            letra + "</div>",
      iconSize: [24, 24], iconAnchor: [12, 12],
    });
  }

  function _crearIconoEmoji(emoji) {
    return L.divIcon({
      className: "",
      html: '<div style="width:34px;height:34px;display:flex;align-items:center;justify-content:center;' +
            'font-size:19px;background:#fff;border-radius:50%;' +
            'box-shadow:0 2px 10px rgba(0,0,0,0.22);border:2px solid rgba(255,255,255,0.9)">' +
            emoji + "</div>",
      iconSize: [34, 34], iconAnchor: [17, 17], popupAnchor: [0, -20],
    });
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
    ta.focus(); ta.select();
    try { document.execCommand("copy"); exito(); } catch (e) {}
    document.body.removeChild(ta);
  }

  return {
    inicializar:             inicializar,
    dibujar:                 dibujar,
    mostrarPuntoCursor:      mostrarPuntoCursor,
    ocultarPuntoCursor:      ocultarPuntoCursor,
    mostrarPois:             mostrarPois,
    limpiarPois:             limpiarPois,
    toggleGradiente:         toggleGradiente,
    invalidarTamano:         invalidarTamano,
    resaltarTramo:           resaltarTramo,
    limpiarTramoResaltado:   limpiarTramoResaltado,
    renderCheckpoints:       renderCheckpoints,
    activarModoCheckpoint:   activarModoCheckpoint,
    desactivarModoCheckpoint: desactivarModoCheckpoint,
  };

})();
