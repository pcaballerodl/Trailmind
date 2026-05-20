document.addEventListener("DOMContentLoaded", function () {

  var dropZone = document.getElementById("drop-zone");
  var inputArchivo = document.getElementById("input-archivo");
  var btnSeleccionar = document.getElementById("btn-seleccionar");
  var spinner = document.getElementById("spinner");
  var mensajeError = document.getElementById("mensaje-error");
  var zonaCarga = document.getElementById("zona-carga");
  var dashboard = document.getElementById("dashboard");
  var btnNuevoTrack = document.getElementById("btn-nuevo-track");
  var btnConsultarMeteo = document.getElementById("btn-consultar-meteo");
  var btnGenerarPlan = document.getElementById("btn-generar-plan");
  var btnBuscarPoi = document.getElementById("btn-buscar-poi");
  var sliderPoi = document.getElementById("poi-radio");

  // Inicializar slider y enlazar actualización en tiempo real
  if (sliderPoi) {
    _actualizarSlider(sliderPoi);
    sliderPoi.addEventListener("input", function () {
      _actualizarSlider(this);
    });
  }

  // Toggles de tipo POI (💧 / ⛺)
  document.querySelectorAll(".poi-toggle").forEach(function (btn) {
    btn.addEventListener("click", function () {
      this.classList.toggle("activo");
    });
  });

  btnSeleccionar.addEventListener("click", function () {
    inputArchivo.click();
  });

  inputArchivo.addEventListener("change", function () {
    if (inputArchivo.files.length > 0) {
      procesarArchivo(inputArchivo.files[0]);
    }
  });

  // Drag & drop
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
    var archivos = e.dataTransfer.files;
    if (archivos.length > 0) {
      procesarArchivo(archivos[0]);
    }
  });

  btnConsultarMeteo.addEventListener("click", function () {
    TrailMind.meteo.cargar();
  });

  btnGenerarPlan.addEventListener("click", function () {
    TrailMind.plan.generar();
  });

  btnBuscarPoi.addEventListener("click", function () {
    TrailMind.poi.buscar();
  });

  btnNuevoTrack.addEventListener("click", function () {
    TrailMind.poi.limpiar();
    dashboard.classList.add("oculto");
    zonaCarga.classList.remove("oculto");
    btnNuevoTrack.classList.add("oculto");
    ocultarError();
    inputArchivo.value = "";
  });

  function procesarArchivo(archivo) {
    ocultarError();

    if (!archivo.name.toLowerCase().endsWith(".gpx")) {
      mostrarError("El archivo debe tener extensión .gpx");
      return;
    }

    mostrarSpinner(true);

    var formData = new FormData();
    formData.append("archivo", archivo);

    fetch("/api/gpx/subir", {
      method: "POST",
      body: formData,
    })
      .then(function (respuesta) { return respuesta.json(); })
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

    // Forzar reflow para que Leaflet calcule dimensiones correctas
    window.dispatchEvent(new Event("resize"));

    TrailMind.mapa.inicializar();
    TrailMind.mapa.dibujar(datos.puntos);
    TrailMind.grafico.dibujar(datos.puntos);
    TrailMind.estadisticas.mostrar(datos);
    TrailMind.meteo.establecerCoordenadas(datos.puntos[0].lat, datos.puntos[0].lon);
    TrailMind.plan.establecerTrack(datos);
    TrailMind.poi.establecerBbox(datos.puntos);
  }

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

  // Actualiza el fondo degradado del slider y la etiqueta de valor
  function _actualizarSlider(slider) {
    var val = parseInt(slider.value, 10);
    var pct = ((val - 100) / (5000 - 100)) * 100;
    slider.style.background =
      "linear-gradient(to right, #2d6a4f 0%, #2d6a4f " + pct + "%, rgba(0,0,0,0.12) " + pct + "%, rgba(0,0,0,0.12) 100%)";
    var labelEl = document.getElementById("poi-radio-valor");
    if (labelEl) {
      labelEl.textContent = val >= 1000
        ? (val % 1000 === 0 ? val / 1000 + " km" : (val / 1000).toFixed(1) + " km")
        : val + " m";
    }
  }

});
