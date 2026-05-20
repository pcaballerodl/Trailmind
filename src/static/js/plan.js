window.TrailMind = window.TrailMind || {};

window.TrailMind.plan = (function () {

  var _resumenTrack = null;  // datos del track sin el array puntos
  var _generando = false;

  function establecerTrack(datos) {
    // Guardar solo el resumen, nunca el array puntos (puede tener miles de elementos)
    _resumenTrack = {
      nombre_track:        datos.nombre_track,
      distancia_km:        datos.distancia_km,
      desnivel_positivo_m: datos.desnivel_positivo_m,
      desnivel_negativo_m: datos.desnivel_negativo_m,
      altitud_max_m:       datos.altitud_max_m,
      altitud_min_m:       datos.altitud_min_m,
      altitud_media_m:     datos.altitud_media_m,
      total_puntos:        datos.total_puntos,
      tiene_timestamps:    datos.tiene_timestamps,
    };
  }

  function generar() {
    if (_generando) return;
    if (!_resumenTrack) {
      _mostrarError("Carga un track GPX antes de generar el plan");
      return;
    }

    var nivel = document.getElementById("plan-nivel").value;
    var dias = parseInt(document.getElementById("plan-dias").value, 10);
    var personas = parseInt(document.getElementById("plan-personas").value, 10);

    if (!nivel || isNaN(dias) || isNaN(personas)) {
      _mostrarError("Rellena todos los campos antes de generar");
      return;
    }

    // Obtener previsión del módulo meteo si está disponible
    var prevision = TrailMind.meteo.obtenerPrevision
      ? TrailMind.meteo.obtenerPrevision()
      : null;

    var cuerpo = {
      track:       _resumenTrack,
      prevision:   prevision,
      preferencias: { dias: dias, nivel: nivel, personas: personas },
    };

    _iniciarGeneracion();

    fetch("/api/ia/plan", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify(cuerpo),
    })
      .then(function (respuesta) {
        if (!respuesta.ok || !respuesta.body) {
          throw new Error("Error en la respuesta del servidor");
        }
        return _leerStream(respuesta.body);
      })
      .catch(function (err) {
        _finalizarGeneracion();
        _mostrarError(err.message || "No se pudo conectar con el servidor");
      });
  }

  function _leerStream(body) {
    var lector = body.getReader();
    var decodificador = new TextDecoder();
    var buffer = "";
    var textoCompleto = "";
    var contenedor = document.getElementById("plan-contenido");

    function leerChunk() {
      return lector.read().then(function (resultado) {
        if (resultado.done) {
          _finalizarGeneracion();
          return;
        }

        buffer += decodificador.decode(resultado.value, { stream: true });

        // Separar eventos SSE por \n\n
        var bloques = buffer.split("\n\n");
        buffer = bloques.pop() || "";

        bloques.forEach(function (bloque) {
          bloque = bloque.trim();
          if (!bloque.startsWith("data: ")) return;
          try {
            var evento = JSON.parse(bloque.slice(6));
            if (evento.tipo === "chunk") {
              textoCompleto += evento.texto;
              // Mostrar texto en crudo durante el streaming con cursor parpadeante
              if (contenedor) contenedor.textContent = textoCompleto + "▋";
            } else if (evento.tipo === "fin") {
              _renderizarMarkdown(contenedor, textoCompleto);
              _finalizarGeneracion();
            } else if (evento.tipo === "error") {
              _finalizarGeneracion();
              _mostrarError(evento.mensaje || "Error al generar el plan");
            }
          } catch (e) { /* ignorar bloques malformados */ }
        });

        return leerChunk();
      });
    }

    return leerChunk();
  }

  function _renderizarMarkdown(contenedor, texto) {
    if (!contenedor) return;
    if (typeof marked !== "undefined") {
      contenedor.innerHTML = marked.parse(texto);
    } else {
      // Fallback si marked no carga
      contenedor.textContent = texto;
    }
  }

  function _iniciarGeneracion() {
    _generando = true;
    var btn = document.getElementById("btn-generar-plan");
    var spinner = document.getElementById("plan-spinner");
    var contenedor = document.getElementById("plan-contenido");
    var errorEl = document.getElementById("plan-error");
    if (btn) btn.disabled = true;
    if (spinner) spinner.classList.remove("oculto");
    if (contenedor) contenedor.textContent = "";
    if (errorEl) errorEl.classList.add("oculto");
  }

  function _finalizarGeneracion() {
    _generando = false;
    var btn = document.getElementById("btn-generar-plan");
    var spinner = document.getElementById("plan-spinner");
    if (btn) btn.disabled = false;
    if (spinner) spinner.classList.add("oculto");
  }

  function _mostrarError(mensaje) {
    var el = document.getElementById("plan-error");
    if (el) {
      el.textContent = mensaje;
      el.classList.remove("oculto");
    }
  }

  return {
    establecerTrack: establecerTrack,
    generar:         generar,
  };

})();
