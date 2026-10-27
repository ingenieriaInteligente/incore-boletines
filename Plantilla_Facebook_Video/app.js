(()=>{'use strict'; const c=window.INCORE_CONFIG;const $=id=>document.getElementById(id);
 const setTitle=(root,text,highlight)=>{root.replaceChildren();let i=highlight?text.indexOf(highlight):-1;if(i<0){root.textContent=text;return;}root.append(document.createTextNode(text.slice(0,i)));let s=document.createElement('span');s.className='highlight';s.textContent=highlight;root.append(s,document.createTextNode(text.slice(i+highlight.length)));};
 const logo=$('logo');if(logo)logo.src=c.logo;
 const tag=$('tag');if(tag)tag.textContent='BOLETÍN TÉCNICO INCORE';
 const sign=$('firma');if(sign){sign.querySelector('strong').textContent=[c.firma.tratamiento,c.firma.nombre].filter(Boolean).join(' ');sign.querySelector('span').textContent=c.firma.credencial;}
 const state=document.body.dataset.state;
 if(state==='portada'){const img=$('coverImg');img.src=c.portadaSocial.modo==='PERSONALIZADA'?c.portadaSocial.imagenPersonalizada:c.portadaSocial.base;img.onerror=()=>{img.src=c.portadaSocial.imagen;};setTitle($('coverTitle'),c.titulo,c.tituloResaltado);$('playIcon').hidden=c.portadaSocial.mostrarPlay===false;$('coverClick').addEventListener('click',()=>{sessionStorage.setItem('incorePlayDesdePortada','1');location.href='video.html';});}
 if(state==='video'){
  const v=$('video'), status=$('videoStatus');
  const setStatus=(message)=>{status.textContent=message;status.hidden=!message;};
  // Sin controles de audio duplicados: solo los controles nativos del reproductor.
  // El navegador puede impedir la reproducción automática con sonido.
  // Solicitar sonido al venir de una interacción explícita con Play.
  // El navegador puede rechazar autoplay con sonido: en ese caso no se oculta el control Play.
  const desdePortada=sessionStorage.getItem('incorePlayDesdePortada')==='1';
  const desdeBoletin=sessionStorage.getItem('incorePlayDesdeBoletin')==='1';
  sessionStorage.removeItem('incorePlayDesdePortada');
  sessionStorage.removeItem('incorePlayDesdeBoletin');
  v.muted=false;
  v.defaultMuted=false;
  v.playsInline=true;
  if(typeof c.video==='string'&&c.video.trim()){
    v.src=c.video;
    // No usar la imagen de portada como poster: se confunde con otra pantalla.
    v.removeAttribute('poster');
    v.addEventListener('error',()=>setStatus('No se pudo cargar el video. Verifica la ruta del MP4 en config.js.'));
    v.addEventListener('loadeddata',()=>setStatus(''));
    if(desdePortada||desdeBoletin){
      v.play().catch(()=>{setStatus('Pulsa Play en el reproductor para iniciar el video con audio.');});
    }
    v.addEventListener('playing',()=>setStatus(''));
  }else setStatus('No se ha configurado el video en config.js.');
}
 if(state==='boletin'){
 const volverVideo=document.querySelector('a[href="video.html"]');
 if(volverVideo) volverVideo.addEventListener('click',()=>sessionStorage.setItem('incorePlayDesdeBoletin','1'));
 let n=1,zoom=1;const viewer=$('viewer'),img=$('page'),counter=$('count');
 function draw(){img.src=c.boletin.carpeta+'/'+c.boletin.prefijo+String(n).padStart(2,'0')+c.boletin.extension;img.alt='Lámina '+n+' de '+c.boletin.totalPaginas;counter.textContent=n+' / '+c.boletin.totalPaginas;$('prev').disabled=n===1;$('next').disabled=n===c.boletin.totalPaginas;apply();}
 function apply(){viewer.classList.toggle('zoomed',zoom>1);img.style.width=zoom>1?(zoom*100)+'%':'100%';img.style.height=zoom>1?'auto':'100%';viewer.scrollTop=0;viewer.scrollLeft=0;$('zoomLabel').textContent=Math.round(zoom*100)+'%';}
 function change(d){const k=Math.max(1,Math.min(c.boletin.totalPaginas,n+d));if(k!==n){n=k;zoom=1;draw();}}
 $('prev').onclick=()=>change(-1);$('next').onclick=()=>change(1);$('zoomIn').onclick=()=>{zoom=Math.min(3,zoom+.25);apply()};$('zoomOut').onclick=()=>{zoom=Math.max(1,zoom-.25);apply()};$('fit').onclick=()=>{zoom=1;apply()};$('full').onclick=()=>{if(!document.fullscreenElement) viewer.requestFullscreen?.();else document.exitFullscreen?.();};
 document.addEventListener('keydown',e=>{if(e.target.closest('input,textarea,button'))return;if(e.key==='ArrowRight'&&zoom===1)change(1);if(e.key==='ArrowLeft'&&zoom===1)change(-1);if(e.key==='+'||e.key==='=')$('zoomIn').click();if(e.key==='-')$('zoomOut').click();});
 let start;viewer.addEventListener('touchstart',e=>{if(e.touches.length!==1||zoom>1){start=null;return;}start={x:e.touches[0].clientX,y:e.touches[0].clientY};},{passive:true});viewer.addEventListener('touchend',e=>{if(!start||!e.changedTouches.length||zoom>1)return;const dx=e.changedTouches[0].clientX-start.x,dy=e.changedTouches[0].clientY-start.y;start=null;if(Math.abs(dx)>55&&Math.abs(dx)>Math.abs(dy)*1.35)change(dx<0?1:-1)},{passive:true});draw();}
})();
