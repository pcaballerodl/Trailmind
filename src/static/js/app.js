document.addEventListener("DOMContentLoaded", function () {

  var dropZone       = document.getElementById("drop-zone");
  var inputArchivo   = document.getElementById("input-archivo");
  var btnSeleccionar = document.getElementById("btn-seleccionar");
  var spinner        = document.getElementById("spinner");
  var mensajeError   = document.getElementById("mensaje-error");
  var zonaCarga      = document.getElementById("zona-carga");
  var dashboard      = document.getElementById("dashboard");
  var btnNuevoTrack       = document.getElementById("btn-nuevo-track");
  var btnConsultarMeteo   = document.getElementById("btn-consultar-meteo");
  var btnGenerarPlan      = document.getElementById("btn-generar-plan");
  var btnBuscarPoi        = document.getElementById("btn-buscar-poi");
  var btnGradiente        = document.getElementById("btn-gradiente");
  var btnPantallaCompleta = document.getElementById("btn-pantalla-completa");
  var btnLimpiarSeleccion = document.getElementById("btn-limpiar-seleccion");
  var selectorModo        = document.getElementById("selector-modo");
  var sliderPoi           = document.getElementById("poi-radio");
  var inputHoraSalida     = document.getElementById("hora-salida");
  var inputItinerarioDias = document.getElementById("itinerario-dias");
  var btnSugerirCheckp    = document.getElementById("btn-sugerir-checkpoints");
  var btnLimpiarCheckp    = document.getElementById("btn-limpiar-checkpoints");
  var btnModoCheckpoint   = document.getElementById("btn-modo-checkpoint");
  var modalCheckpoint     = document.getElementById("modal-checkpoint");
  var btnModalOk          = document.getElementById("modal-cp-ok");
  var btnModalCancelar    = document.getElementById("modal-cp-cancelar");

  // ── Slider radio POI ────────────────────────────────────────────────────────
  if (sliderPoi) {
    _actualizarSlider(sliderPoi);
    sliderPoi.addEventListener("input", function () { _actualizarSlider(this); });
  }

  // ── Toggles visuales de tipo POI y gradiente ────────────────────────────────
  document.querySelectorAll(".poi-toggle").forEach(function (btn) {
    btn.addEventListener("click", function () { this.classList.toggle("activo"); });
  });

  // ── Gradiente ───────────────────────────────────────────────────────────────
  if (btnGradiente) {
    btnGradiente.addEventListener("click", function () {
      TrailMind.mapa.toggleGradiente();
    });
  }

  // ── Pantalla completa ────────────────────────────────────────────────────────
  if (btnPantallaCompleta) {
    btnPantallaCompleta.addEventListener("click", function () {
      dashboard.classList.toggle("mapa-completo");
      setTimeout(function () { TrailMind.mapa.invalidarTamano(); }, 50);
    });
  }

  // ── Selector modo tiempo (óptimo / desfavorable) ────────────────────────────
  if (selectorModo) {
    selectorModo.addEventListener("change", function () {
      TrailMind.estimacion.setModo(this.value);
      TrailMind.itinerario.setModo(this.value);
    });
  }

  // ── Hora de salida ────────────────────────────────────────────────────────────
  if (inputHoraSalida) {
    inputHoraSalida.addEventListener("change", function () {
      TrailMind.itinerario.setHoraSalida(this.value);
    });
  }

  // ── Días del track ───────────────────────────────────────────────────────────
  // (se lee en tiempo real al pulsar "Sugerir")

  // ── Sugerir checkpoints ──────────────────────────────────────────────────────
  if (btnSugerirCheckp) {
    btnSugerirCheckp.addEventListener("click", function () {
      var dias = parseInt(inputItinerarioDias ? inputItinerarioDias.value : "1", 10) || 1;
      TrailMind.itinerario.sugerir(dias);
    });
  }

  // ── Limpiar checkpoints ──────────────────────────────────────────────────────
  if (btnLimpiarCheckp) {
    btnLimpiarCheckp.addEventListener("click", function () {
      TrailMind.itinerario.limpiar();
    });
  }

  // ── Modo añadir checkpoint manual ────────────────────────────────────────────
  if (btnModoCheckpoint) {
    btnModoCheckpoint.addEventListener("click", function () {
      var activo = btnModoCheckpoint.classList.toggle("activo");
      TrailMind.itinerario.setModoAnadir(activo);
      if (activo) {
        TrailMind.mapa.activarModoCheckpoint();
      } else {
        TrailMind.mapa.desactivarModoCheckpoint();
      }
    });
  }

  // ── Modal checkpoint ─────────────────────────────────────────────────────────
  function cerrarModal() {
    if (modalCheckpoint) modalCheckpoint.classList.add("oculto");
  }

  if (btnModalOk) {
    btnModalOk.addEventListener("click", function () {
      var tipo     = document.getElementById("modal-cp-tipo");
      var etiqueta = document.getElementById("modal-cp-etiqueta");
      var duracion = document.getElementById("modal-cp-duracion");
      var lat      = parseFloat(document.getElementById("modal-cp-lat").value);
      var lon      = parseFloat(document.getElementById("modal-cp-lon").value);
      var indice   = parseInt(document.getElementById("modal-cp-indice").value, 10);
      var km       = parseFloat(document.getElementById("modal-cp-km").value);
      var alt      = parseFloat(document.getElementById("modal-cp-alt").value);

      if (isNaN(indice)) { cerrarModal(); return; }

      TrailMind.itinerario.agregarManual({
        tipo:        tipo     ? tipo.value         : "poi",
        etiqueta:    etiqueta ? etiqueta.value      : "",
        duracion_min: duracion ? parseInt(duracion.value, 10) || 15 : 15,
        lat:         isNaN(lat) ? null : lat,
        lon:         isNaN(lon) ? null : lon,
        indice:      indice,
        km_acum:     isNaN(km)  ? 0   : km,
        alt_m:       isNaN(alt) ? null : alt,
      });
      cerrarModal();
    });
  }

  if (btnModalCancelar) {
    btnModalCancelar.addEventListener("click", cerrarModal);
  }

  if (modalCheckpoint) {
    modalCheckpoint.addEventListener("click", function (e) {
      if (e.target === modalCheckpoint) cerrarModal();
    });
  }

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") cerrarModal();
  });

  // ── Limpiar selección de tramo ───────────────────────────────────────────────
  if (btnLimpiarSeleccion) {
    btnLimpiarSeleccion.addEventListener("click", function () {
      TrailMind.grafico.limpiarSeleccion();
    });
  }

  // ── Carga de archivos ────────────────────────────────────────────────────────
  btnSeleccionar.addEventListener("click", function () { inputArchivo.click(); });

  inputArchivo.addEventListener("change", function () {
    if (inputArchivo.files.length > 0) procesarArchivo(inputArchivo.files[0]);
  });

  dropZone.addEventListener("dragover", function (e) {
    e.preventDefault();
    dropZone.classList.add("arrastrando");
  });
  dropZone.addEventListener("dragleave", function () {
    dropZone.classList.remove("arrastrando");
  });
  dropZone.addEventListener("drop", function (e) {
    e.preventDefault();
    dropZone.classList.remove("arrastrando");
    if (e.dataTransfer.files.length > 0) procesarArchivo(e.dataTransfer.files[0]);
  });

  // ── Botones de acción ────────────────────────────────────────────────────────
  btnConsultarMeteo.addEventListener("click", function () { TrailMind.meteo.cargar(); });
  btnGenerarPlan.addEventListener("click",    function () { TrailMind.plan.generar(); });
  btnBuscarPoi.addEventListener("click",      function () { TrailMind.poi.buscar(); });

  btnNuevoTrack.addEventListener("click", function () {
    TrailMind.poi.limpiar();
    TrailMind.itinerario.limpiar();
    if (btnModoCheckpoint) btnModoCheckpoint.classList.remove("activo");
    TrailMind.mapa.desactivarModoCheckpoint();
    dashboard.classList.remove("mapa-completo");
    dashboard.classList.add("oculto");
    zonaCarga.classList.remove("oculto");
    btnNuevoTrack.classList.add("oculto");
    ocultarError();
    inputArchivo.value = "";
  });

  // ── Procesamiento de track ───────────────────────────────────────────────────

  function procesarArchivo(archivo) {
    ocultarError();
    if (!archivo.name.toLowerCase().endsWith(".gpx")) {
      mostrarError("El archivo debe tener extensión .gpx");
      return;
    }
    mostrarSpinner(true);
    var formData = new FormData();
    formData.append("archivo", archivo);

    fetch("/api/gpx/subir", { method: "POST", body: formData })
      .then(function (r) { return r.json(); })
      .then(function (json) {
        mostrarSpinner(false);
        if (json.ok) {
          mostrarDashboard(json.datos);
        } else {
          mostrarError(json.error || "Error al procesar el archivo");
        }
      })
      .catch(function () {
        mostrarSpinner(false);
        mostrarError("No se pudo conectar con el servidor");
      });
  }

  function mostrarDashboard(datos) {
    zonaCarga.classList.add("oculto");
    dashboard.classList.remove("oculto");
    btnNuevoTrack.classList.remove("oculto");

    // Restablecer controles
    if (btnGradiente)    btnGradiente.classList.remove("activo");
    if (btnModoCheckpoint) btnModoCheckpoint.classList.remove("activo");
    if (selectorModo)    selectorModo.value = "optimo";
    if (inputHoraSalida) inputHoraSalida.value = "08:00";
    TrailMind.mapa.desactivarModoCheckpoint();

    window.dispatchEvent(new Event("resize"));

    TrailMind.mapa.inicializar();
    TrailMind.mapa.dibujar(datos.puntos);
    TrailMind.grafico.dibujar(datos.puntos);
    TrailMind.estadisticas.mostrar(datos);
    TrailMind.meteo.establecerCoordenadas(datos.puntos[0].lat, datos.puntos[0].lon);
    TrailMind.plan.establecerTrack(datos);
    TrailMind.poi.establecerBbox(datos.puntos);
    TrailMind.estimacion.establecerTrack(datos);
    TrailMind.estimacion.cargar();
    TrailMind.estimacion.cargarTramos(datos.puntos);
  }

  // ── Utilidades ────────────────────────────────────────────────────────────────

  function mostrarSpinner(visible) {
    spinner.classList.toggle("oculto", !visible);
    btnSeleccionar.disabled = visible;
  }

  function mostrarError(mensaje) {
    mensajeError.textContent = mensaje;
    mensajeError.classList.remove("oculto");
  }

  function ocultarError() {
    mensajeError.classList.add("oculto");
    mensajeError.textContent = "";
  }

  function _actualizarSlider(slider) {
    var val = parseInt(slider.value, 10);
    var pct = ((val - 100) / (5000 - 100)) * 100;
    slider.style.background =
      "linear-gradient(to right, #2d6a4f 0%, #2d6a4f " + pct +
      "%, rgba(0,0,0,0.12) " + pct + "%, rgba(0,0,0,0.12) 100%)";
    var labelEl = document.getElementById("poi-radio-valor");
    if (labelEl) {
      labelEl.textContent = val >= 1000
        ? (val % 1000 === 0 ? val / 1000 + " km" : (val / 1000).toFixed(1) + " km")
        : val + " m";
    }
  }

});
