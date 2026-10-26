"""Generador INCORE v0.5: AUTO / PERSONALIZADA, portada base 4:5 y OG social."""
from pathlib import Path
import re,sys,math,subprocess
try:
 import cv2
 from PIL import Image,ImageDraw,ImageFont
except ImportError:
 sys.exit('FAIL | instalar: python -m pip install opencv-python pillow')
R=Path(__file__).resolve().parent
s=(R/'config.js').read_text(encoding='utf-8')
def get(k,default=''):
 m=re.search(r'\b'+re.escape(k)+r'\s*:\s*["\']([^"\']+)["\']',s)
 return m.group(1) if m else default
mode=get('modo','AUTO').upper()
video=R/get('video','videos/presentacion.mp4')
custom=R/get('imagenPersonalizada','assets/portada-personalizada.png')
base=R/get('base','assets/portada-base.png')
og=R/get('imagen','assets/portada-social-facebook.png')
base.parent.mkdir(parents=True,exist_ok=True);og.parent.mkdir(parents=True,exist_ok=True)
def fill(im,w,h):
 scale=max(w/im.width,h/im.height)
 im=im.convert('RGB').resize((math.ceil(scale*im.width),math.ceil(scale*im.height)),Image.Resampling.LANCZOS)
 x=(im.width-w)//2;y=(im.height-h)//2
 return im.crop((x,y,x+w,y+h))
if mode=='AUTO':
 if not video.is_file():sys.exit('FAIL | MP4 no existe: '+str(video))
 cap=cv2.VideoCapture(str(video));fps=cap.get(cv2.CAP_PROP_FPS);count=cap.get(cv2.CAP_PROP_FRAME_COUNT)
 if not cap.isOpened() or fps<=0 or count<=0:sys.exit('FAIL | video no legible')
 duration=count/fps; best=(-1e99,0)
 for i in range(24):
  t=duration*(.12+.76*i/23)
  cap.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,frame=cap.read()
  if not ok:continue
  gray=cv2.cvtColor(cv2.resize(frame,(320,200)),cv2.COLOR_BGR2GRAY)
  light=float(gray.mean()); sharp=float(cv2.Laplacian(gray,cv2.CV_64F).var());contrast=float(gray.std())
  score=min(sharp,600)*.35+contrast*1.5-abs(light-125)*.6
  if not 35<light<225:score-=500
  if score>best[0]:best=(score,t)
 cap.release()
 if best[0]==-1e99:sys.exit('FAIL | sin fotogramas')
 temporary=R/'assets'/'_fotograma_temp.png'
 try:subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(best[1]),'-i',str(video),'-frames:v','1',str(temporary)],check=True)
 except (OSError,subprocess.CalledProcessError):sys.exit('FAIL | FFmpeg')
 with Image.open(temporary) as im:fill(im,1080,1350).save(base)
 temporary.unlink(missing_ok=True)
 print(f'AUTO | segundo {best[1]:.2f} de {duration:.2f}')
elif mode=='PERSONALIZADA':
 if not custom.is_file():sys.exit('FAIL | falta '+str(custom))
 with Image.open(custom) as im:fill(im,1080,1350).save(base)
else:sys.exit('FAIL | modo inválido: '+mode)
# Composición de portada final 4:5, con título, Play y miniatura PNG-01.
with Image.open(base) as source:
 im=source.convert('RGBA')
overlay=Image.new('RGBA',im.size,(0,0,0,0));d=ImageDraw.Draw(overlay)
for y in range(1350):
 strength=int(205*(1-y/1350)**2 + 60*(y/1350)**5)
 d.line((0,y,1080,y),fill=(2,18,34,min(210,strength)))
im=Image.alpha_composite(im,overlay);d=ImageDraw.Draw(im)
font_path=next((p for p in ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf','C:/Windows/Fonts/arialbd.ttf'] if Path(p).exists()),None)
def font(size):return ImageFont.truetype(font_path,size) if font_path else ImageFont.load_default()
title=get('titulo','Boletín técnico INCORE');hi=get('tituloResaltado','')
def wrap_title(value,limit=960):
 words=value.split();lines=[];current=''
 for word in words:
  candidate=(current+' '+word).strip()
  if current and d.textbbox((0,0),candidate,font=font(58))[2]>limit:
   lines.append(current);current=word
  else:current=candidate
 if current:lines.append(current)
 return lines
# Segmenta la frase resaltada incluso cuando ocupa más de una línea.
def draw_colored_line(line,x,y):
 if not hi or hi not in title:
  d.text((x,y),line,font=font(58),fill='white',stroke_width=2,stroke_fill='#021222');return
 # Coincidencia exacta del tramo destacado, sin colorear palabras repetidas fuera de él.
 position=x
 line_start=title.find(line)
 hi_start=title.find(hi)
 hi_end=hi_start+len(hi)
 for match in re.finditer(r'\S+',line):
  word=match.group()
  word_start=line_start+match.start()
  color='#FC7C00' if hi_start>=0 and hi_start<=word_start<hi_end else 'white'
  d.text((position,y),word,font=font(58),fill=color,stroke_width=2,stroke_fill='#021222')
  position+=d.textlength(word+' ',font=font(58))
d.text((42,44),'INCORE · BOLETÍN TÉCNICO',font=font(26),fill='#00AAFA')
for i,line in enumerate(wrap_title(title)[:6]): draw_colored_line(line,42,112+i*75)
# Miniatura en la esquina inferior derecha, íntegra y sin deformación.
mini=R/'imagenes'/'pagina_01.png'
if not mini.is_file():sys.exit('FAIL | falta miniatura '+str(mini))
with Image.open(mini) as source:
 thumb=source.convert('RGBA');thumb.thumbnail((322,413),Image.Resampling.LANCZOS)
px=1080-thumb.width-42;py=1350-thumb.height-42
shade=Image.new('RGBA',(thumb.width+14,thumb.height+14),(2,18,34,180))
im.alpha_composite(shade,(px-7,py-7));im.alpha_composite(thumb,(px,py))
d=ImageDraw.Draw(im)
if not re.search(r'\bmostrarPlay\s*:\s*false',s):
 x,y=540,750
 d.ellipse((x-78,y-78,x+78,y+78),fill=(2,18,34,190),outline='white',width=5)
 d.polygon([(x-22,y-37),(x-22,y+37),(x+43,y)],fill='white')
im.convert('RGB').save(og,optimize=True)
webroot=get('baseUrl','https://ingenieriainteligente.github.io/incore-boletines/Plantilla_Facebook_Video/').rstrip('/')+'/'
html=R/'compartir.html'; t=html.read_text(encoding='utf-8')
for key,val in [('og:title',title),('og:url',webroot+'compartir.html'),('og:image',webroot+og.relative_to(R).as_posix())]:
 val=val.replace('&','&amp;').replace('"','&quot;').replace('<','&lt;')
 t=re.sub('(<meta property="'+key+'" content=")[^"]*(")',lambda m:m[1]+val+m[2],t)
html.write_text(t,encoding='utf-8')
print('PASS | '+str(base.relative_to(R))+' | '+str(og.relative_to(R))+' | compartir.html')
