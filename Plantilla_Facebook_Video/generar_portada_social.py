#!/usr/bin/env python3
"""INCORE v0.4: fotograma social automático y actualización OG. Requiere Python 3, OpenCV y FFmpeg.
Ejecutar desde la carpeta Plantilla_Facebook_Video: python generar_portada_social.py
"""
from pathlib import Path
import cv2, subprocess, re, sys
ROOT=Path(__file__).resolve().parent
CFG=(ROOT/'config.js').read_text(encoding='utf-8')
def field(name,default=''):
    match=re.search(r'\b'+re.escape(name)+r'\s*:\s*[\"\']([^\"\']+)[\"\']',CFG)
    return match.group(1) if match else default
src=ROOT/field('video','videos/presentacion.mp4')
out=ROOT/'assets'/'portada-social-facebook.png'
if not src.is_file(): sys.exit(f'ERROR: no se encontró el MP4: {src}')
cap=cv2.VideoCapture(str(src))
fps=cap.get(cv2.CAP_PROP_FPS); frames=cap.get(cv2.CAP_PROP_FRAME_COUNT)
if not fps or not frames: sys.exit('ERROR: No se pudo interpretar el MP4.')
duration=frames/fps
# Muestras distribuidas entre 12% y 88% del video; evita intros/outros y fotogramas negros.
start=max(0.5,duration*.12); end=duration*.88
n=15
scores=[]
for i in range(n):
    sec=start+(end-start)*i/(n-1)
    cap.set(cv2.CAP_PROP_POS_MSEC,sec*1000)
    ok,frame=cap.read()
    if not ok: continue
    h,w=frame.shape[:2]
    scale=480/max(w,h)
    sm=cv2.resize(frame,(max(2,round(w*scale)),max(2,round(h*scale))))
    hsv=cv2.cvtColor(sm,cv2.COLOR_BGR2HSV)
    gray=cv2.cvtColor(sm,cv2.COLOR_BGR2GRAY)
    brightness=gray.mean(); contrast=gray.std(); sharpness=cv2.Laplacian(gray,cv2.CV_64F).var()
    saturation=hsv[:,:,1].mean(); clipping=(gray<18).mean()+(gray>242).mean()
    # Heurística visual, NO comprensión semántica: nitidez, contraste, exposición, color.
    if brightness<35 or brightness>225: continue
    score=min(sharpness,1100)*.17+contrast*.8+saturation*.30-220*clipping
    scores.append((score,sec))
cap.release()
if not scores: sys.exit('ERROR: No hay fotogramas suficientemente legibles.')
score,sec=max(scores)
out.parent.mkdir(exist_ok=True)
# Escalar + recortar central a 1200x630 sin deformar ni agregar texto/controles.
filter='crop=iw:trunc(ih*0.86/2)*2:0:0,scale=1200:630:force_original_aspect_ratio=increase,crop=1200:630,setsar=1'
cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',f'{sec:.3f}','-i',str(src),'-frames:v','1','-vf',filter,str(out)]
try: subprocess.run(cmd,check=True)
except FileNotFoundError: sys.exit('ERROR: instalar FFmpeg y agregarlo al PATH.')
except subprocess.CalledProcessError: sys.exit('ERROR: Falló la extracción del fotograma.')
html=ROOT/'compartir.html'
s=html.read_text(encoding='utf-8')
# Ruta relativa usada por la página como publicación web. OG requiere URL absoluta.
url='https://ingenieriainteligente.github.io/incore-boletines/Plantilla_Facebook_Video/assets/portada-social-facebook.png'
s=re.sub(r'(<meta property="og:image(?:\:secure_url)?" content=")[^"]*(")',lambda m:m.group(1)+url+m.group(2),s)
s=re.sub(r'(<meta property="og:image:alt" content=")[^"]*(")',lambda m:m.group(1)+'Fotograma del video introductorio del boletín técnico INCORE'+m.group(2),s)
html.write_text(s,encoding='utf-8')
print(f'PASS | Fotograma elegido: {sec:.2f}s de {duration:.2f}s | archivo {out} | metadatos preparados')
