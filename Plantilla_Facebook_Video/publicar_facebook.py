#!/usr/bin/env python3
"""Publicación explícita de portada social en una Página de Facebook (no perfiles)."""
import os
import sys
from pathlib import Path
import requests
from PIL import Image

ROOT = Path(__file__).resolve().parent
PHOTO = ROOT / 'assets' / 'portada-social-facebook.png'
PAGE_ID = os.getenv('FB_PAGE_ID', '').strip()
TOKEN = os.getenv('FB_PAGE_ACCESS_TOKEN', '').strip()
VERSION = 'v26.0'
PUBLIC_URL = 'https://ingenieriainteligente.github.io/incore-boletines/Plantilla_Facebook_Video/compartir.html'


def fail(msg):
    raise SystemExit('FAIL | ' + msg)


def main():
    if os.getenv('CONFIRMAR_PUBLICACION') != 'PUBLICAR':
        fail('publicación no autorizada: falta confirmación explícita PUBLICAR')
    if not PAGE_ID.isdigit() or not TOKEN:
        fail('falta configurar FB_PAGE_ID o FB_PAGE_ACCESS_TOKEN en GitHub Actions Secrets')
    if not PHOTO.is_file():
        fail('falta generar assets/portada-social-facebook.png')
    with Image.open(PHOTO) as pic:
        if pic.size != (1080, 1350):
            fail('la portada no tiene 1080 × 1350 px')
        if pic.format != 'PNG':
            fail('la portada debe ser PNG')
    if PHOTO.stat().st_size > 9 * 1024 * 1024:
        fail('imagen superior a 9 MiB; optimizar antes de publicar')
    title = os.getenv('FB_PUBLICACION_TEXTO', '').strip()
    if not title:
        title = 'Boletín técnico INCORE · Construcción de una Línea de Transmisión de 500 kV'
    caption = f'{title}\n\nConsulta el video y el boletín técnico completo:\n{PUBLIC_URL}'
    endpoint = f'https://graph.facebook.com/{VERSION}/{PAGE_ID}/photos'
    try:
        with PHOTO.open('rb') as f:
            r = requests.post(endpoint, data={'caption': caption, 'published': 'true'},
                              files={'source': (PHOTO.name, f, 'image/png')},
                              headers={'Authorization': f'Bearer {TOKEN}'}, timeout=90)
        data = r.json()
    except (requests.RequestException, ValueError) as exc:
        fail(f'error de solicitud a Facebook ({type(exc).__name__})')
    if not r.ok:
        err = data.get('error', {}) if isinstance(data, dict) else {}
        # Deliberadamente no exponer token ni respuesta completa.
        fail(f"Meta Graph API HTTP {r.status_code} | código {err.get('code', 'sin código')} | tipo {err.get('type', 'error')}")
    photo_id = data.get('id')
    post_id = data.get('post_id')
    if not photo_id:
        fail('Meta no devolvió ID de fotografía: verificar publicación manualmente')
    print('PASS | fotografía publicada en la Página de Facebook')
    print('PHOTO_ID |', photo_id)
    if post_id:
        print('POST_ID |', post_id)
    print('ENLACE_BOLETIN |', PUBLIC_URL)


if __name__ == '__main__':
    main()
