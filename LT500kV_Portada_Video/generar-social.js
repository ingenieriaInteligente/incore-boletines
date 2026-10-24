'use strict';
// INCORE — Generador social. Sin dependencias. Ejecutar: node generar-social.js
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const cp = require('child_process');
const os = require('os');
const crypto = require('crypto');
const root = process.cwd();
const configPath = path.join(root, 'config.js');
const fail = msg => { console.error('ERROR: ' + msg); process.exit(1); };
if (!fs.existsSync(configPath)) fail('No se encuentra config.js en esta carpeta.');
const sandbox = {window:{}};
try { vm.runInNewContext(fs.readFileSync(configPath,'utf8'),sandbox,{timeout:1500,filename:'config.js'}); }
catch(e) { fail('No se pudo leer config.js: '+e.message); }
const c = sandbox.window.INCORE_CONFIG;
if (!c || typeof c !== 'object') fail('Falta window.INCORE_CONFIG en config.js');
const s = c.social;
if (!s || typeof s !== 'object') fail('Falta el bloque social: {...} en config.js');
if (!s.baseSitio || !/^https:\/\//.test(String(s.baseSitio))) fail('social.baseSitio debe comenzar por https://');
const folder = String(s.carpetaPublicacion || path.basename(root)).trim();
if (!/^[A-Za-z0-9_-]+$/.test(folder)) fail('Nombre de carpeta inválido: '+folder);
const image = String(s.imagen || 'assets/portada-social.jpg').replace(/\\/g,'/');
if (image.startsWith('/') || image.includes('..') || !/\.(jpe?g|png|webp)$/i.test(image)) fail('social.imagen debe ser ruta relativa válida de JPG, PNG o WebP.');
// Social Cover Generator v2.0.3: generar JPG desde pagina_01 (no se edita la portada manualmente).
const firstPage = path.join(root, String(c.carpetaImagenes || 'imagenes'),
  String(c.prefijoPagina || 'pagina_') + '01.' + String(c.extension || 'png'));
if (!fs.existsSync(firstPage)) fail('No se encuentra la primera lámina: '+firstPage);
if (!fs.existsSync(path.join(root, 'generar-portada.ps1'))) fail('Falta generar-portada.ps1 en la carpeta.');
const titleCover = String(s.tituloPortada || c.subtitulo || c.titulo || '').trim();
if (!titleCover) fail('Falta título para portada: configure social.tituloPortada o titulo.');
const metaFile = path.join(os.tmpdir(), 'incore-social-'+process.pid+'.json');
try {
  fs.writeFileSync(metaFile, JSON.stringify({root, cover:path.relative(root,firstPage), output:image, logo:String(c.logo || 'assets/logo-incore.png'),title:titleCover,author:String(c.autor || '').trim()}), 'utf8');
  const result = cp.spawnSync('powershell.exe', ['-NoProfile','-ExecutionPolicy','Bypass','-File',path.join(root,'generar-portada.ps1'),'-MetadataPath',metaFile], {encoding:'utf8', windowsHide:false});
  if (result.status !== 0) fail('No pudo generarse portada-social.jpg. '+(result.stderr||result.stdout||result.error));
  process.stdout.write(result.stdout || 'PASS: Portada social generada.\n');
} finally {try {fs.unlinkSync(metaFile);} catch (_) {}}
if (!fs.existsSync(path.join(root,image))) fail('No se generó la portada '+image);
const base = String(s.baseSitio).replace(/\/+$/,'')+'/';
const url = base+encodeURIComponent(folder)+'/';
const page = url+'compartir.html';
// Version basada en el contenido real de la imagen, no en la fecha ni el nombre.
// Si el JPG cambia, Meta recibe una URL og:image nueva automaticamente.
const imageHash = crypto.createHash('sha256').update(fs.readFileSync(path.join(root, image))).digest('hex').slice(0, 16);
// Copia con nombre unico por contenido. No se modifica portada-social.jpg ni se eliminan versiones antiguas.
const parsedImage = path.posix.parse(image);
const versionedImage = path.posix.join(parsedImage.dir, parsedImage.name + '-' + imageHash + parsedImage.ext);
const originalBytes = fs.readFileSync(path.join(root, image));
const versionedPath = path.join(root, versionedImage);
if (!fs.existsSync(versionedPath)) {
  fs.copyFileSync(path.join(root, image), versionedPath, fs.constants.COPYFILE_EXCL);
} else {
  const existingHash = crypto.createHash('sha256').update(fs.readFileSync(versionedPath)).digest('hex').slice(0, 16);
  if (existingHash !== imageHash) fail('La copia versionada existente no coincide: ' + versionedPath);
}
const imageUrl = url + versionedImage.split('/').map(encodeURIComponent).join('/');
const title = String(s.titulo || c.titulo || 'Boletín técnico INCORE').trim();
const description = String(s.descripcion || c.subtitulo || 'Boletín técnico interactivo de INCORE Knowledge Studio').trim();
if (!title || !description) fail('El título y la descripción social no deben estar vacíos.');
const esc = v => String(v).replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
const html = `<!doctype html>
<html lang="es"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(title)}</title>
<meta name="description" content="${esc(description)}">
<link rel="canonical" href="${esc(page)}">
<meta property="og:type" content="website"><meta property="og:locale" content="es_PE">
<meta property="og:site_name" content="INCORE Knowledge Studio">
<meta property="og:title" content="${esc(title)}"><meta property="og:description" content="${esc(description)}">
<meta property="og:url" content="${esc(page)}">
<meta property="og:image" content="${esc(imageUrl)}">
<meta property="og:image:secure_url" content="${esc(imageUrl)}">
<meta property="og:image:alt" content="${esc(title)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="${esc(title)}">
<meta name="twitter:description" content="${esc(description)}">
<meta name="twitter:image" content="${esc(imageUrl)}">
<script>
// Redireccion temprana: no cargar imagenes ni mostrar la tarjeta social.
// El rastreador de Meta lee las etiquetas OG del head sin ejecutar JS.
window.location.replace('./');
</script>
</head><body>
<noscript><p>Para abrir el boletin, <a href="./">haz clic aqui</a>.</p></noscript>
</body></html>
`;
fs.writeFileSync(path.join(root,'compartir.html'),html,'utf8');
console.log('PASS: compartir.html generado.');
console.log('URL PARA FACEBOOK: '+page);
console.log('PORTADA: '+imageUrl);
console.log('ARCHIVO SOCIAL VERSIONADO: '+versionedImage);
console.log('VERSION DE IMAGEN: '+imageHash);
console.log('Sube compartir.html y '+versionedImage+' a GitHub. NO elimines imagenes sociales previas.');
