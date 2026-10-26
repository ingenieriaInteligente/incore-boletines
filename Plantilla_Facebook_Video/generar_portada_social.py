# -*- coding: utf-8 -*-
"""
Generador INCORE v0.5.2
- Portada social 4:5
- Modo AUTO / PERSONALIZADA
- Genera:
    1) assets/portada-base.png
    2) assets/portada-social-facebook.png
- Actualiza compartir.html (og:title, og:url, og:image)
"""

from pathlib import Path
import re
import sys
import math
import subprocess

try:
    import cv2
    from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
except ImportError:
    sys.exit("FAIL | instalar dependencias: python -m pip install opencv-python pillow")


# =========================================================
# RUTAS BASE
# =========================================================
ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config.js"
HTML_COMPARTIR = ROOT / "compartir.html"


# =========================================================
# UTILIDADES DE LECTURA DE config.js
# =========================================================
def read_text_file(path: Path) -> str:
    if not path.is_file():
        sys.exit(f"FAIL | no existe el archivo: {path}")
    return path.read_text(encoding="utf-8")


config_text = read_text_file(CONFIG)


def get_string(key: str, default: str = "") -> str:
    """
    Busca una clave tipo:
    key: "valor"
    key: 'valor'
    """
    pattern = rf'\b{re.escape(key)}\s*:\s*["\']([^"\']+)["\']'
    m = re.search(pattern, config_text, re.MULTILINE)
    return m.group(1).strip() if m else default


def get_bool(key: str, default: bool = True) -> bool:
    """
    Busca una clave tipo:
    key: true
    key: false
    """
    pattern = rf'\b{re.escape(key)}\s*:\s*(true|false)'
    m = re.search(pattern, config_text, re.IGNORECASE | re.MULTILINE)
    if not m:
        return default
    return m.group(1).lower() == "true"


# =========================================================
# PARÁMETROS DESDE config.js
# =========================================================
MODO = get_string("modo", "AUTO").upper()

VIDEO = ROOT / get_string("video", "videos/presentacion.mp4")
IMAGEN_PERSONALIZADA = ROOT / get_string("imagenPersonalizada", "assets/portada-personalizada.png")

PORTADA_BASE = ROOT / get_string("base", "assets/portada-base.png")
PORTADA_SOCIAL = ROOT / get_string("imagen", "assets/portada-social-facebook.png")

TITULO = get_string("titulo", "Construcción de una Línea de Transmisión de 500 kV")
TITULO_RESALTADO = get_string("tituloResaltado", "Línea de Transmisión de 500 kV")

BASE_URL = get_string(
    "baseUrl",
    "https://ingenieriainteligente.github.io/incore-boletines/Plantilla_Facebook_Video/"
).rstrip("/") + "/"

MOSTRAR_PLAY = get_bool("mostrarPlay", True)

MINIATURA_BOLETIN = ROOT / "imagenes" / "pagina_01.png"

PORTADA_BASE.parent.mkdir(parents=True, exist_ok=True)
PORTADA_SOCIAL.parent.mkdir(parents=True, exist_ok=True)


# =========================================================
# CONSTANTES VISUALES
# =========================================================
W = 1080
H = 1350

COLOR_AZUL = "#00AAFA"
COLOR_NARANJA = "#FC7C00"
COLOR_FONDO_OSCURO = "#021222"
COLOR_BLANCO = "#FFFFFF"


# =========================================================
# FUENTES
# =========================================================
def find_font_file() -> str | None:
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/Arialbd.ttf",
        "C:/Windows/Fonts/segoeuib.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            return p
    return None


FONT_FILE = find_font_file()


def load_font(size: int):
    if FONT_FILE:
        return ImageFont.truetype(FONT_FILE, size=size)
    return ImageFont.load_default()


# =========================================================
# UTILIDADES DE IMAGEN
# =========================================================
def crop_fill(im: Image.Image, width: int, height: int) -> Image.Image:
    """
    Llena el lienzo sin deformar (crop tipo cover).
    """
    scale = max(width / im.width, height / im.height)
    new_w = math.ceil(im.width * scale)
    new_h = math.ceil(im.height * scale)
    im = im.convert("RGB").resize((new_w, new_h), Image.Resampling.LANCZOS)
    x = (new_w - width) // 2
    y = (new_h - height) // 2
    return im.crop((x, y, x + width, y + height))


def rounded_mask(size: tuple[int, int], radius: int) -> Image.Image:
    m = Image.new("L", size, 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)
    return m


def draw_top_overlay(im: Image.Image) -> Image.Image:
    """
    Sombra suave superior + leve oscurecimiento general para legibilidad.
    """
    overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)

    for y in range(H):
        # oscurecimiento gradual superior y leve fondo general
        top_strength = int(170 * max(0, 1 - y / 720))
        base_strength = 42
        alpha = min(220, top_strength + base_strength)
        d.line((0, y, W, y), fill=(2, 18, 34, alpha))

    return Image.alpha_composite(im.convert("RGBA"), overlay)


# =========================================================
# EXTRACCIÓN DE FOTOGRAMA REPRESENTATIVO (AUTO)
# =========================================================
def score_frame(frame) -> float:
    """
    Puntaje heurístico:
    - nitidez
    - contraste
    - iluminación equilibrada
    """
    small = cv2.resize(frame, (320, 200))
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

    light = float(gray.mean())
    sharp = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    contrast = float(gray.std())

    score = min(sharp, 600) * 0.35 + contrast * 1.5 - abs(light - 125) * 0.6

    if not (35 < light < 225):
        score -= 500

    return score


def extract_best_frame_from_video(video_path: Path, out_path: Path) -> None:
    if not video_path.is_file():
        sys.exit(f"FAIL | MP4 no existe: {video_path}")

    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)

    if not cap.isOpened() or fps <= 0 or total_frames <= 0:
        sys.exit("FAIL | video no legible")

    duration = total_frames / fps
    best_score = -1e99
    best_time = None

    # analiza 24 muestras entre 12% y 88% del video
    for i in range(24):
        t = duration * (0.12 + 0.76 * i / 23)
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, frame = cap.read()
        if not ok:
            continue

        score = score_frame(frame)
        if score > best_score:
            best_score = score
            best_time = t

    cap.release()

    if best_time is None:
        sys.exit("FAIL | no se pudo seleccionar un fotograma representativo")

    temp_frame = ROOT / "assets" / "_fotograma_temp.png"

    try:
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel", "error",
                "-y",
                "-ss", str(best_time),
                "-i", str(video_path),
                "-frames:v", "1",
                str(temp_frame),
            ],
            check=True
        )
    except OSError:
        sys.exit("FAIL | FFmpeg no está disponible en el sistema")
    except subprocess.CalledProcessError:
        sys.exit("FAIL | FFmpeg no pudo extraer el fotograma")

    with Image.open(temp_frame) as im:
        crop_fill(im, W, H).save(out_path)

    temp_frame.unlink(missing_ok=True)
    print(f"AUTO | segundo {best_time:.2f} de {duration:.2f}")


# =========================================================
# GENERAR PORTADA BASE
# =========================================================
def generate_base_cover() -> None:
    if MODO == "AUTO":
        extract_best_frame_from_video(VIDEO, PORTADA_BASE)

    elif MODO == "PERSONALIZADA":
        if not IMAGEN_PERSONALIZADA.is_file():
            sys.exit(f"FAIL | falta imagen personalizada: {IMAGEN_PERSONALIZADA}")

        with Image.open(IMAGEN_PERSONALIZADA) as im:
            crop_fill(im, W, H).save(PORTADA_BASE)

    else:
        sys.exit(f"FAIL | modo inválido: {MODO}")


# =========================================================
# WRAP DEL TÍTULO EN 3 LÍNEAS
# =========================================================
def split_title_lines(draw: ImageDraw.ImageDraw, title: str, max_width: int, font) -> list[str]:
    """
    Intenta distribuir el título en máximo 3 líneas.
    """
    words = title.split()
    if not words:
        return [""]

    lines = []
    current = ""

    for word in words:
        test = (current + " " + word).strip()
        bbox = draw.textbbox((0, 0), test, font=font, stroke_width=2)
        line_width = bbox[2] - bbox[0]

        if current and line_width > max_width:
            lines.append(current)
            current = word
        else:
            current = test

    if current:
        lines.append(current)

    # si salen más de 3 líneas, fusionar desde abajo
    while len(lines) > 3:
        lines[-2] = lines[-2] + " " + lines[-1]
        lines.pop()

    return lines


def draw_colored_title_line(
    draw: ImageDraw.ImageDraw,
    full_title: str,
    highlighted: str,
    line_text: str,
    x: int,
    y: int,
    font
):
    """
    Dibuja una línea coloreando en naranja solo el tramo que pertenezca
    al texto resaltado.
    """
    if not highlighted or highlighted not in full_title:
        draw.text(
            (x, y),
            line_text,
            font=font,
            fill=COLOR_BLANCO,
            stroke_width=2,
            stroke_fill=COLOR_FONDO_OSCURO
        )
        return

    line_start = full_title.find(line_text)
    hi_start = full_title.find(highlighted)
    hi_end = hi_start + len(highlighted)

    cursor_x = x

    for m in re.finditer(r'\S+\s*', line_text):
        token = m.group()
        word_start = line_start + m.start()

        color = COLOR_NARANJA if (hi_start <= word_start < hi_end) else COLOR_BLANCO

        draw.text(
            (cursor_x, y),
            token,
            font=font,
            fill=color,
            stroke_width=2,
            stroke_fill=COLOR_FONDO_OSCURO
        )
        cursor_x += draw.textlength(token, font=font)


# =========================================================
# DIBUJAR MINIATURA DEL BOLETÍN
# =========================================================
def paste_bulletin_thumbnail(canvas: Image.Image) -> None:
    if not MINIATURA_BOLETIN.is_file():
        sys.exit(f"FAIL | falta miniatura del boletín: {MINIATURA_BOLETIN}")

    with Image.open(MINIATURA_BOLETIN) as src:
        thumb = src.convert("RGBA")

        # más grande que antes
        thumb.thumbnail((345, 460), Image.Resampling.LANCZOS)

        # bordes curvos
        mask = rounded_mask(thumb.size, 24)
        thumb.putalpha(mask)

        px = W - thumb.width - 38
        py = H - thumb.height - 42

        # sombra suave (sin marco)
        shadow = Image.new("RGBA", (thumb.width + 20, thumb.height + 20), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        sd.rounded_rectangle(
            (10, 10, thumb.width + 10, thumb.height + 10),
            radius=28,
            fill=(2, 18, 34, 105)
        )
        shadow = shadow.filter(ImageFilter.GaussianBlur(6))

        canvas.alpha_composite(shadow, (px - 10, py - 10))
        canvas.alpha_composite(thumb, (px, py))


# =========================================================
# DIBUJAR PLAY
# =========================================================
def draw_center_play(draw: ImageDraw.ImageDraw) -> None:
    if not MOSTRAR_PLAY:
        return

    x, y = 540, 675  # centro exacto de 1080x1350

    draw.ellipse(
        (x - 78, y - 78, x + 78, y + 78),
        fill=(2, 18, 34, 205),
        outline="white",
        width=5
    )
    draw.polygon(
        [(x - 22, y - 37), (x - 22, y + 37), (x + 43, y)],
        fill="white"
    )


# =========================================================
# GENERAR PORTADA SOCIAL FINAL
# =========================================================
def generate_social_cover() -> None:
    if not PORTADA_BASE.is_file():
        sys.exit(f"FAIL | no existe portada base: {PORTADA_BASE}")

    with Image.open(PORTADA_BASE) as source:
        im = source.convert("RGBA")
        im = draw_top_overlay(im)

        d = ImageDraw.Draw(im)

        font_header = load_font(26)
        font_title = load_font(58)

        # cabecera
        d.text((42, 44), "INCORE · BOLETÍN TÉCNICO", font=font_header, fill=COLOR_AZUL)

        # título en máx. 3 líneas
        title_lines = split_title_lines(d, TITULO, max_width=960, font=font_title)

        title_y0 = 112
        line_gap = 64  # más compacto

        for i, line in enumerate(title_lines[:3]):
            y = title_y0 + i * line_gap
            draw_colored_title_line(d, TITULO, TITULO_RESALTADO, line, 42, y, font_title)

        # botón play centrado
        draw_center_play(d)

        # miniatura del boletín
        paste_bulletin_thumbnail(im)

        im.convert("RGB").save(PORTADA_SOCIAL, optimize=True)

    print(f"PASS | {PORTADA_SOCIAL.relative_to(ROOT)}")


# =========================================================
# ACTUALIZAR META TAGS DE compartir.html
# =========================================================
def update_og_tags() -> None:
    if not HTML_COMPARTIR.is_file():
        sys.exit(f"FAIL | no existe compartir.html: {HTML_COMPARTIR}")

    html = HTML_COMPARTIR.read_text(encoding="utf-8")

    def esc(v: str) -> str:
        return (
            v.replace("&", "&amp;")
             .replace('"', "&quot;")
             .replace("<", "&lt;")
        )

    og_title = esc(TITULO)
    og_url = esc(BASE_URL + "compartir.html")
    og_image = esc(BASE_URL + PORTADA_SOCIAL.relative_to(ROOT).as_posix())

    replacements = {
        "og:title": og_title,
        "og:url": og_url,
        "og:image": og_image,
    }

    for prop, value in replacements.items():
        pattern = rf'(<meta\s+property="{re.escape(prop)}"\s+content=")[^"]*(")'
        html = re.sub(pattern, rf'\1{value}\2', html)

    HTML_COMPARTIR.write_text(html, encoding="utf-8")
    print("PASS | compartir.html actualizado")


# =========================================================
# MAIN
# =========================================================
def main():
    print("INCORE | Generando portada social...")

    generate_base_cover()
    print(f"PASS | {PORTADA_BASE.relative_to(ROOT)}")

    generate_social_cover()
    update_og_tags()

    print(
        "PASS | "
        f"{PORTADA_BASE.relative_to(ROOT)} | "
        f"{PORTADA_SOCIAL.relative_to(ROOT)} | "
        "compartir.html"
    )


if __name__ == "__main__":
    main()