"""
file_storage.py
Sistema de guardado de páginas generadas en disco (uploads/).
Guarda cada página como .html y .json, y mantiene un índice global index.json.

Identificador único: {fecha}_{tipo-sitio}_{session_corta}
Ejemplo: 2026-02-19_landing_a3f2b1
"""

import os
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Carpeta base donde se guardan los archivos
# Sube dos niveles desde app/services/ hasta la raíz, luego /uploads
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'uploads'))
INDEX_FILE = os.path.join(BASE_DIR, 'index.json')


def _ensure_dirs():
    """Crea la carpeta uploads/ si no existe."""
    os.makedirs(BASE_DIR, exist_ok=True)


def _build_page_id(site_type: str, session_id: str) -> str:
    """
    Construye el identificador único de la página.
    Formato: YYYY-MM-DD_{site_type}_{6 primeros chars del session_id}
    Ejemplo: 2026-02-19_landing_a3f2b1
    """
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    session_short = session_id[:6] if len(session_id) >= 6 else session_id
    # Limpiamos caracteres no válidos en nombres de archivo
    safe_type = "".join(c for c in site_type.lower() if c.isalnum() or c == "-")
    return f"{date_str}_{safe_type}_{session_short}"


def _make_unique_id(page_id: str) -> str:
    """
    Si el page_id ya existe en el índice, añade un sufijo numérico.
    Ejemplo: 2026-02-19_landing_a3f2b1 → 2026-02-19_landing_a3f2b1_2
    """
    index = _load_index()
    existing_ids = {entry["page_id"] for entry in index}

    if page_id not in existing_ids:
        return page_id

    counter = 2
    while f"{page_id}_{counter}" in existing_ids:
        counter += 1
    return f"{page_id}_{counter}"


def _load_index() -> list:
    """Carga el índice global desde index.json. Devuelve lista vacía si no existe."""
    if not os.path.exists(INDEX_FILE):
        return []
    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error leyendo index.json: {e}")
        return []


def _save_index(index: list):
    """Guarda el índice global en index.json."""
    try:
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    except IOError as e:
        logger.error(f"Error escribiendo index.json: {e}")


def save_page(
    html: str,
    prompt: str,
    site_type: str,
    session_id: str,
) -> dict:
    """
    Guarda la página generada como .html y .json en uploads/.
    Actualiza el índice global index.json.

    Devuelve un dict con los metadatos del archivo guardado.
    """
    _ensure_dirs()

    # Construir ID único
    base_id = _build_page_id(site_type, session_id)
    page_id = _make_unique_id(base_id)

    # Rutas de archivo
    html_filename = f"{page_id}.html"
    json_filename = f"{page_id}.json"
    html_path = os.path.join(BASE_DIR, html_filename)
    json_path = os.path.join(BASE_DIR, json_filename)

    # Metadatos
    now = datetime.now(timezone.utc).isoformat()
    metadata = {
        "page_id": page_id,
        "site_type": site_type,
        "prompt": prompt,
        "session_id": session_id,
        "created_at": now,
        "html_file": html_filename,
        "json_file": json_filename,
    }

    # Guardar .html
    try:
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        logger.info(f"HTML guardado: {html_filename}")
    except IOError as e:
        logger.error(f"Error guardando HTML: {e}")
        raise

    # Guardar .json (metadatos + html embebido)
    json_data = {**metadata, "html": html}
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        logger.info(f"JSON guardado: {json_filename}")
    except IOError as e:
        logger.error(f"Error guardando JSON: {e}")
        raise

    # Actualizar índice global
    index = _load_index()
    index.append(metadata)
    _save_index(index)
    logger.info(f"Índice actualizado: {len(index)} páginas registradas")

    return metadata


def list_pages(session_id: str = None) -> list:
    """
    Lista todas las páginas del índice.
    Si se pasa session_id, filtra por esa sesión.
    """
    index = _load_index()
    if session_id:
        return [p for p in index if p.get("session_id") == session_id]
    return index


def get_page(page_id: str) -> dict | None:
    """
    Devuelve los metadatos + HTML de una página por su page_id.
    Lee el .json correspondiente.
    """
    json_path = os.path.join(BASE_DIR, f"{page_id}.json")
    if not os.path.exists(json_path):
        return None
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error leyendo {page_id}.json: {e}")
        return None
