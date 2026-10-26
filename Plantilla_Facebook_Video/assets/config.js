// INCORE · Plantilla_Facebook_Video · v0.5.5
// Conserva el contrato de configuración usado por app.js.
window.INCORE_CONFIG = {
  titulo: "Construcción de una Línea de Transmisión de 500 kV",
  tituloResaltado: "Línea de Transmisión de 500 kV",
  logo: "assets/logo-incore.png",
  video: "videos/presentacion.mp4",

  portadaSocial: {
    modo: "PERSONALIZADA", // AUTO | PERSONALIZADA
    imagen: "assets/portada-social-facebook.png",
    imagenPersonalizada: "assets/portada-personalizada.png",
    base: "assets/portada-base.png",
    miniaturaBoletin: "imagenes/pagina_01.png",
    formato: "4:5",
    mostrarPlay: true,
    priorizarAccion: true, // movimiento estimado, NO detección semántica
    priorizarInicio: true, // revisar primero el tramo inicial para todos los boletines
    inicioDesdePorcentaje: 5, // porcentaje de duración; configurable por proyecto
    inicioHastaPorcentaje: 38,
    calidadMinimaInicio: 70, // evita fotogramas borrosos u oscuros
    muestrasInicio: 24,
    muestrasRespaldo: 32,
    tituloAnchoPorcentaje: 65,
    tituloMaxLineas: 3,
    miniaturaEscala: 1.24
  },

  firma: {
    tratamiento: "Ing.",
    nombre: "Rildo Liden Salazar Buendía",
    credencial: "CIP 87144"
  },
  boletin: {
    carpeta: "imagenes",
    prefijo: "pagina_",
    extension: ".png",
    totalPaginas: 9
  },
  publicar: {
    baseUrl: "https://ingenieriainteligente.github.io/incore-boletines/Plantilla_Facebook_Video/",
    descripcion: "Presentación audiovisual y acceso directo al boletín técnico INCORE."
  }
};
