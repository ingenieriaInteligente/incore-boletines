/* INCORE v0.5.13 — extensión no invasiva de interfaz */
(() => {
  'use strict';
  const c = window.INCORE_CONFIG || {};
  const total = Number(c.boletin?.totalPaginas);
  const state = document.body?.dataset.state;
  const root = document.querySelector('.shell');
  if (!root || !['portada', 'video', 'boletin'].includes(state)) return;

  const phrase = window.INCORE_CIERRE || {lineas: []};
  if (Array.isArray(phrase.lineas) && phrase.lineas.length && !root.querySelector('.incore-cierre')) {
    const aside = document.createElement('aside');
    aside.className = 'incore-cierre';
    aside.setAttribute('aria-label', 'Frase de cierre temática');
    for (const line of phrase.lineas.slice(0, 3)) {
      const p = document.createElement('p');
      const value = String(line);
      const mark = String(phrase.fraseResaltada || '');
      const offset = mark ? value.indexOf(mark) : -1;
      if (offset >= 0) {
        p.append(document.createTextNode(value.slice(0, offset)));
        const span = document.createElement('span');
        span.className = 'incore-frase-resaltada';
        span.textContent = mark;
        p.append(span, document.createTextNode(value.slice(offset + mark.length)));
      } else {
        p.textContent = value;
      }
      aside.appendChild(p);
    }
    root.appendChild(aside);
  }

  if (state !== 'boletin') return;
  const toolbar = root.querySelector('.toolbar');
  const count = document.getElementById('count');
  if (!toolbar || !count || !Number.isInteger(total) || total < 1) {
    console.warn('INCORE v0.5.13: faltan controles o totalPaginas válido');
    return;
  }
  // Mover el control Video preexistente: nunca duplicarlo.
  const existingVideo = Array.from(root.querySelectorAll('a[href]')).find(a => {
    try { return new URL(a.getAttribute('href'), location.href).pathname.endsWith('/video.html'); }
    catch { return false; }
  });
  const actions = document.createElement('div');
  actions.className = 'incore-acciones-boletin';
  actions.setAttribute('aria-label', 'Acciones del boletín');
  const video = existingVideo || document.createElement('a');
  if (!existingVideo) video.href = 'video.html';
  video.classList.add('control', 'incore-accion');
  video.textContent = '▶ Video';
  actions.appendChild(video);
  // Regresar al video desde el boletín conserva la señal de navegación original.
  video.addEventListener('click', () => sessionStorage.setItem('incorePlayDesdeBoletin', '1'));

  const share = document.createElement('button');
  share.type = 'button';
  share.className = 'control incore-accion incore-solo-final';
  share.textContent = '↗ Compartir';
  share.hidden = true;
  share.setAttribute('aria-label', 'Compartir enlace directo al boletín');
  share.addEventListener('click', async () => {
    const baseUrl = c.publicar?.baseUrl;
if (!baseUrl || !/^https:\/\/[^ ]+$/i.test(baseUrl)) {
  alert('No se ha configurado una dirección pública válida para compartir.');
  return;
}
const url = new URL('boletin.html', baseUrl).href;
    const data = { title: c.titulo || 'Boletín técnico INCORE', text: 'Boletín técnico INCORE', url };
    try {
      if (location.protocol !== 'file:' && navigator.share) { await navigator.share(data); return; }
      if (navigator.clipboard?.writeText) { await navigator.clipboard.writeText(url); alert('Enlace del boletín copiado.'); return; }
      prompt('Copia el enlace del boletín:', url);
    } catch (err) { if (err?.name !== 'AbortError') prompt('Copia el enlace del boletín:', url); }
  });
  actions.appendChild(share);

  const download = document.createElement('a');
  download.className = 'primary incore-accion incore-solo-final';
  download.href = 'descargas/boletin-completo.pdf';
  download.download = 'INCORE-Boletin-Tecnico.pdf';
  download.textContent = '↓ Descargar';
  download.hidden = true;
  download.setAttribute('aria-label', 'Descargar boletín completo en PDF');
  actions.appendChild(download);
  toolbar.insertAdjacentElement('afterend', actions);

  function update() {
    const page = Number((count.textContent || '').match(/^\s*(\d+)\s*\//)?.[1]);
    const last = page === total;
    share.hidden = !last;
    download.hidden = !last;
  }
  new MutationObserver(update).observe(count, { childList: true, characterData: true, subtree: true });
  update();
})();
