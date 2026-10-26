// INCORE · Plantilla_Facebook_Video · v0.5.3
// Conserva el contrato de configuración usado por app.js.
window.INCORE_CONFIG = {
  titulo: "Construcción de una Línea de Transmisión de 500 kV",
  tituloResaltado: "Línea de Transmisión de 500 kV",
  logo: "assets/logo-incore.png",
  video: "videos/presentacion.mp4",

  portadaSocial: {
    modo: "AUTO", // AUTO | PERSONALIZADA
    imagen: "assets/portada-social-facebook.png",
    imagenPersonalizada: "assets/portada-personalizada.png",
    base: "assets/portada-base.png",
    miniaturaBoletin: "imagenes/pagina_01.png",
    formato: "4:5",
    mostrarPlay: true,
    priorizarAccion: true, // heurística de movimiento, no detección semántica de trabajadores
    tituloAnchoPorcentaje: 75,
    tituloMaxLineas: 3,
    miniaturaEscala: 1.12
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
