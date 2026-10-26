# -*- coding: utf-8 -*-
"""INCORE v0.5.4 · Portada 4:5 AUTO/PERSONALIZADA para GitHub Actions."""
from __future__ import annotations

from pathlib import Path
import math
import re
import subprocess
import sys

try:
    import cv2
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except ImportError:
    sys.exit("FAIL | instalar: python -m pip install opencv-python pillow")

ROOT = Path(__file__).resolve().parent
W, H = 1080, 1350
AZUL, NARANJA, OSCURO = "#00AAFA", "#FC7C00", "#021222"


def fail(message):
    raise SystemExit(f"FAIL | {message}")


def section(text, key):
    """Leer una sección simple de objeto JS, compatible con config.js actual."""
    match = re.search(r"\b" + re.escape(key) + r"\s*:\s*\{", text)
    if not match:
        fail(f"falta sección de configuración: {key}")
    begin = match.end()
    end = text.find("}", begin)
    if end < 0:
        fail(f"sección incompleta: {key}")
    return text[begin:end]


def string(text, key, default=""):
    m = re.search(r"\b" + re.escape(key) + r"\s*:\s*([\"'])(.*?)\1", text)
    return m.group(2) if m else default


def number(text, key, default):
    m = re.search(r"\b" + re.escape(key) + r"\s*:\s*(-?\d+(?:\.\d+)?)", text)
    return float(m.group(1)) if m else default


def boolean(text, key, default):
    m = re.search(r"\b" + re.escape(key) + r"\s*:\s*(true|false)\b", text)
    return m.group(1) == "true" if m else default


config_path = ROOT / "config.js"
if not config_path.is_file():
    fail(f"no existe {config_path}")
source = config_path.read_text(encoding="utf-8")
cover_cfg = section(source, "portadaSocial")
pub_cfg = section(source, "publicar")
TITLE = string(source, "titulo", "Boletín técnico INCORE")
HIGHLIGHT = string(source, "tituloResaltado", "")
MODE = string(cover_cfg, "modo", "AUTO").upper()
VIDEO = ROOT / string(source, "video", "videos/presentacion.mp4")
PERSONAL = ROOT / string(cover_cfg, "imagenPersonalizada", "assets/portada-personalizada.png")
BASE = ROOT / string(cover_cfg, "base", "assets/portada-base.png")
FINAL = ROOT / string(cover_cfg, "imagen", "assets/portada-social-facebook.png")
THUMB = ROOT / string(cover_cfg, "miniaturaBoletin", "imagenes/pagina_01.png")
SHOW_PLAY = boolean(cover_cfg, "mostrarPlay", True)
ACTION = boolean(cover_cfg, "priorizarAccion", True)
TITLE_WIDTH_PCT = max(40, min(90, number(cover_cfg, "tituloAnchoPorcentaje", 65)))
MAX_LINES = max(1, min(5, int(number(cover_cfg, "tituloMaxLineas", 3))))
THUMB_SCALE = max(.7, min(1.3, number(cover_cfg, "miniaturaEscala", 1.24)))
BASE_URL = string(pub_cfg, "baseUrl", "https://ingenieriainteligente.github.io/incore-boletines/Plantilla_Facebook_Video/").rstrip("/") + "/"

for path in (BASE, FINAL):
    if ROOT not in path.resolve().parents:
        fail(f"ruta fuera del proyecto: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)


def cover_fill(im):
    im = im.convert("RGB")
    scale = max(W / im.width, H / im.height)
    w, h = math.ceil(scale * im.width), math.ceil(scale * im.height)
    im = im.resize((w, h), Image.Resampling.LANCZOS)
    return im.crop(((w - W)//2, (h-H)//2, (w + W)//2, (h + H)//2))


def quality(frame):
    gray = cv2.cvtColor(cv2.resize(frame, (320, 200)), cv2.COLOR_BGR2GRAY)
    bright = float(gray.mean())
    sharp = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    contrast = float(gray.std())
    q = min(sharp, 600) * .35 + contrast * 1.5 - abs(bright - 125) * .6
    return q - 500 if not (35 < bright < 225) else q


def movement(cap, t, frame, duration):
    """Movimiento visual aproximado: puede incluir movimiento de cámara."""
    cap.set(cv2.CAP_PROP_POS_MSEC, min(duration - .04, t + .20) * 1000)
    ok, nxt = cap.read()
    if not ok:
        return 0.0
    a = cv2.cvtColor(cv2.resize(frame, (160, 120)), cv2.COLOR_BGR2GRAY)
    b = cv2.cvtColor(cv2.resize(nxt, (160, 120)), cv2.COLOR_BGR2GRAY)
    # Diferencia promedio tras suavizado: reducir ruido de compresión.
    a = cv2.GaussianBlur(a, (5, 5), 0)
    b = cv2.GaussianBlur(b, (5, 5), 0)
    return float(cv2.absdiff(a, b).mean())


def generate_base():
    if MODE == "PERSONALIZADA":
        if not PERSONAL.is_file():
            fail(f"falta portada personalizada: {PERSONAL}")
        with Image.open(PERSONAL) as im:
            cover_fill(im).save(BASE)
        print("PERSONALIZADA | imagen de base cargada")
        return
    if MODE != "AUTO":
        fail(f"modo inválido: {MODE}")
    if not VIDEO.is_file():
        fail(f"MP4 no existe: {VIDEO}")
    cap = cv2.VideoCapture(str(VIDEO))
    if not cap.isOpened():
        fail("OpenCV no pudo abrir MP4")
    fps = float(cap.get(cv2.CAP_PROP_FPS))
    frames = float(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if fps <= 0 or frames <= 0:
        cap.release()
        fail("no se pudieron leer FPS y duración")
    duration = frames / fps
    best = None
    # 32 instantes entre el 10 y 90 %, sin depender de una posición fija.
    for i in range(32):
        t = duration * (.10 + .80 * i / 31)
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, frame = cap.read()
        if not ok:
            continue
        q = quality(frame)
        motion = movement(cap, t, frame, duration) if ACTION else 0
        # Bonus acotado: el movimiento ayuda pero no vence a una imagen borrosa.
        score = q + min(35.0, motion * 2.0) if ACTION else q
        if best is None or score > best[0]:
            best = (score, t, q, motion)
    cap.release()
    if best is None:
        fail("no se encontraron fotogramas válidos")
    temp = BASE.parent / "_fotograma_temp.png"
    try:
        subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-ss", f"{best[1]:.3f}", "-i", str(VIDEO), "-frames:v", "1", str(temp)
        ], check=True, capture_output=True)
        with Image.open(temp) as im:
            cover_fill(im).save(BASE)
    except (OSError, subprocess.CalledProcessError) as e:
        fail(f"FFmpeg no pudo extraer el fotograma: {e}")
    finally:
        temp.unlink(missing_ok=True)
    print(f"AUTO | segundo {best[1]:.2f}/{duration:.2f} | calidad={best[2]:.1f} | movimiento={best[3]:.1f}")


def font(size):
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/segoeuib.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ]
    p = next((p for p in candidates if Path(p).exists()), None)
    return ImageFont.truetype(p, size) if p else ImageFont.load_default()


def title_layout(draw):
    """Ajusta fuente hasta tener <= MAX_LINES sin sobrepasar ancho real."""
    words = TITLE.split()
    if not words:
        fail("título vacío")
    width = round(W * TITLE_WIDTH_PCT / 100)
    for fontsize in range(58, 27, -2):
        f = font(fontsize)
        # Si el resaltado es una frase final, separar el texto base y repartir
        # la frase destacada entre las líneas restantes cuando sea posible.
        hi = " ".join(HIGHLIGHT.split())
        if MAX_LINES == 3 and hi and TITLE.endswith(hi):
            plain = TITLE[:-len(hi)].strip()
            hwords = hi.split()
            if plain and len(hwords) >= 2 and draw.textlength(plain, font=f) <= width:
                candidate_lines = []
                for cut in range(1, len(hwords)):
                    first = " ".join(hwords[:cut]); second = " ".join(hwords[cut:])
                    if max(draw.textlength(first, font=f), draw.textlength(second, font=f)) <= width:
                        # Favorece cortes entre unidades editoriales de la frase.
                        penalty = abs(draw.textlength(first, font=f) - draw.textlength(second, font=f))
                        candidate_lines.append((penalty, [plain, first, second]))
                if candidate_lines:
                    _, parts = min(candidate_lines, key=lambda item: item[0])
                    words0 = TITLE.split()
                    blocks = []
                    offset = 0
                    for part in parts:
                        length = len(part.split()); blocks.append((offset, offset + length, part))
                        offset += length
                    return f, words0, blocks
        if any(draw.textlength(word, font=f) > width for word in words):
            continue
        # Optimizar equilibrio entre las líneas (programación dinámica por cortes).
        n = len(words)
        dp = {(0, 0): (0.0, [])}
        for line_count in range(1, MAX_LINES + 1):
            for end in range(1, n + 1):
                choices = []
                for start in range(end):
                    prev = dp.get((line_count - 1, start))
                    if prev is None:
                        continue
                    text = " ".join(words[start:end])
                    tw = draw.textlength(text, font=f)
                    if tw > width:
                        continue
                    penalty = (width - tw)**2 / width**2
                    choices.append((prev[0] + penalty, prev[1] + [(start, end, text)]))
                if choices:
                    dp[(line_count, end)] = min(choices, key=lambda x: x[0])
        if not any((k, n) in dp for k in range(1, MAX_LINES+1)):
            continue
        # Preferir tres líneas bien equilibradas cuando el título lo permite.
        k = MAX_LINES if (MAX_LINES, n) in dp else max(k for k in range(1, MAX_LINES+1) if (k, n) in dp)
        return f, words, dp[(k, n)][1]
    fail("el título no cabe con tamaño mínimo 28 px; revisa título/ancho")


def draw_title(draw):
    f, words, lines = title_layout(draw)
    normalized = " ".join(words)
    hi = " ".join(HIGHLIGHT.split())
    hi_start = normalized.find(hi) if hi else -1
    hi_end = hi_start + len(hi)
    starts = []
    pos = 0
    for word in words:
        starts.append(pos)
        pos += len(word) + 1
    line_height = max(30, round(f.size * 0.96))  # interlineado editorial compacto
    for i, (a, b, text) in enumerate(lines):
        x, y = 42.0, 106 + i * line_height
        for j in range(a, b):
            word = words[j]
            is_hi = hi_start >= 0 and hi_start <= starts[j] < hi_end
            color = NARANJA if is_hi else "#FFFFFF"
            draw.text((round(x), y), word, font=f, fill=color,
                      stroke_width=1, stroke_fill=OSCURO)
            x += draw.textlength(word + " ", font=f)
    print(f"TÍTULO | {len(lines)} líneas | ancho {TITLE_WIDTH_PCT:g}% | fuente {f.size}px")


def rounded_thumbnail(im):
    if not THUMB.is_file():
        fail(f"falta miniatura: {THUMB}")
    with Image.open(THUMB) as raw:
        thumb = raw.convert("RGBA")
    max_w = round(345 * THUMB_SCALE)
    max_h = round(460 * THUMB_SCALE)
    thumb.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
    mask = Image.new("L", thumb.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, thumb.width - 1, thumb.height - 1), radius=25, fill=255)
    thumb.putalpha(mask)
    px, py = W - thumb.width - 38, H - thumb.height - 42
    shadow = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        (px + 3, py + 5, px + thumb.width + 3, py + thumb.height + 5),
        radius=25, fill=(2, 18, 34, 110))
    im.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(10)))
    im.alpha_composite(thumb, (px, py))


def generate_final():
    with Image.open(BASE) as raw:
        im = raw.convert("RGBA")
    overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for y in range(H):
        alpha = min(225, int(42 + 170 * max(0, 1 - y / 720)))
        d.line((0, y, W, y), fill=(2, 18, 34, alpha))
    im = Image.alpha_composite(im, overlay)
    draw = ImageDraw.Draw(im)
    draw.text((42, 42), "INCORE · BOLETÍN TÉCNICO", font=font(26), fill=AZUL)
    draw_title(draw)
    if SHOW_PLAY:
        x, y = W//2, H//2
        draw.ellipse((x-78, y-78, x+78, y+78),
                     fill=(2, 18, 34, 205), outline="#FFFFFF", width=5)
        draw.polygon([(x-22, y-37), (x-22, y+37), (x+43, y)], fill="#FFFFFF")
    rounded_thumbnail(im)
    im.convert("RGB").save(FINAL, optimize=True)


def update_og():
    path = ROOT / "compartir.html"
    if not path.is_file():
        fail("no existe compartir.html")
    html = path.read_text(encoding="utf-8")
    def escape(value):
        return value.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")
    try:
        image_rel = FINAL.relative_to(ROOT).as_posix()
    except ValueError:
        fail("ruta final fuera del proyecto")
    fields = {
        "og:title": TITLE,
        "og:url": BASE_URL + "compartir.html",
        "og:image": BASE_URL + image_rel,
        "og:image:width": str(W),
        "og:image:height": str(H),
    }
    for key, val in fields.items():
        pattern = r'(<meta\s+property=["\']' + re.escape(key) + r'["\']\s+content=["\'])([^"\']*)(["\'])'
        html, count = re.subn(pattern, lambda m: m.group(1) + escape(val) + m.group(3), html, count=1)
        if count != 1:
            fail(f"etiqueta {key} no encontrada en compartir.html")
    path.write_text(html, encoding="utf-8")


def main():
    generate_base()
    generate_final()
    update_og()
    for p in (BASE, FINAL):
        with Image.open(p) as im:
            if im.size != (W, H):
                fail(f"dimensiones incorrectas: {p.name}")
    print("PASS | portada-base.png | portada-social-facebook.png | compartir.html")


if __name__ == "__main__":
    main()
