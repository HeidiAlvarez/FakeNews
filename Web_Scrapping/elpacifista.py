import requests
import pandas as pd
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

import os
from dotenv import load_dotenv

load_dotenv()

namespace = os.getenv('URL_ElPACIFISTA')


def get_urls_Pacifista(sitemap_url: str, headers: dict):
    """
    Descarga y parsea el sitemap de Pacifista.tv y retorna todas las URLs
    correspondientes a artículos válidos.

    1. Descarga el XML del sitemap.
    2. Extrae los <loc>.
    3. Filtra:
        - imágenes
        - archivos estáticos
        - elementos que no sean artículos

    Retorna:
        list[str]: lista de URLs limpias.
    """
    resp = requests.get(sitemap_url, headers=headers)

    if resp.status_code != 200:
        print(f"Error HTTP {resp.status_code} al acceder a {sitemap_url}")
        return []

    try:
        root = ET.fromstring(resp.content)
    except Exception as e:
        print("Error parseando XML:", e)
        return []

#    namespace = "{http://www.sitemaps.org/schemas/sitemap/0.9}"

    urls = [
    url_tag.find(f"{namespace}loc").text
    for url_tag in root.findall(f"{namespace}url")
]

    clean_urls = []
    for u in urls:
        u_l = u.lower()

        # Filtrar imágenes o assets
        if "/wp-content/" in u_l:
            continue
        if u_l.endswith((".jpg", ".png", ".jpeg", ".gif", ".webp")):
            continue

        # Evitar spam en cirílico (patrones comunes %d0%, %d1%, %d2%)
        if "%d0%" in u_l or "%d1%" in u_l or "%d2%" in u_l:
            continue

        # Evitar palabras rusas
        if ("став" in u_l or "спорт" in u_l or "казин" in u_l 
            or "букм" in u_l or "онлайн" in u_l):
            continue

        # Evitar caracteres NO ASCII (cirílico real)
        try:
            u.encode("ascii")
        except UnicodeEncodeError:
            continue

        # Filtrar para que solo queden secciones reales del medio
        if not any(
            x in u_l for x in 
            ["actualidad", "memoria", "violencias", "derechos", "post", "podcast", "blog"]
        ):
            continue

        clean_urls.append(u)

    return clean_urls


def get_article_info_Pacifista(url: str, headers: dict):
    """
    Descarga y parsea una noticia de Pacifista.tv.

    Extrae:
        - title
        - subtitle (si existe)
        - date_published
        - body (texto completo)
        - author
        - tags
        - sección (Pacifista no tiene secciones, se retorna 'general')

    La estructura del HTML de Pacifista no es estable, por lo que se incluyen
    múltiples estrategias de fallback para cada elemento.
    """
    resp = requests.get(url, headers=headers)

    if resp.status_code != 200:
        print(f"Error HTTP {resp.status_code} al acceder a {url}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    
    # TÍTULO
    title_tag = soup.find("h1")
    if not title_tag:
        title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else None

    # SUBTÍTULO
    subtitle_tag = (
        soup.find("h2", class_="subtitle")
        or soup.find("div", class_="subtitle")
        or soup.find("p", class_="subtitle")
    )

    if subtitle_tag:
        subtitle = subtitle_tag.get_text(strip=True)
    else:
        meta_desc = soup.find("meta", attrs={"name": "description"})
        subtitle = meta_desc["content"].strip() if meta_desc else None

    # FECHA
    meta_date = soup.find("meta", attrs={"property": "article:published_time"})
    if meta_date and meta_date.get("content"):
        date_published = meta_date["content"]
    else:
        time_tag = soup.find("time")
        date_published = time_tag.get_text(strip=True) if time_tag else None

    # AUTOR
    meta_author = soup.find("meta", attrs={"name": "author"})
    if meta_author and meta_author.get("content"):
        author = meta_author["content"].strip()
    else:
        a_author = soup.find("a", rel="author")
        author = a_author.get_text(strip=True) if a_author else None

    # CUERPO
    container = (
        soup.find("div", class_="entry-content")
        or soup.find("div", class_="post-content")
        or soup.find("article")
    )

    if container:
        parrafos = [
            p.get_text(" ", strip=True)
            for p in container.find_all("p")
            if p.get_text(strip=True)
        ]
        body = "\n".join(parrafos) if parrafos else None
    else:
        body = None

    # TAGS
    tag_elements = soup.find_all("a", rel="tag")
    tags = [t.get_text(strip=True) for t in tag_elements] if tag_elements else None

    # Sección fija
    section = "general"

    return {
        "url": url,
        "title": title,
        "subtitle": subtitle,
        "date_published": date_published,
        "body": body,
        "author": author,
        "section": section,
        "tags": tags,
    }


def get_news_Pacifista(sitemap_url: str, headers: dict, limit: int = None):
    """
    Procesa el sitemap de Pacifista.tv y retorna un DataFrame con varias noticias.

    Pasos:
        1. Extraer URLs desde el sitemap.
        2. Aplicar un límite si se especifica.
        3. Descargar y parsear cada artículo.
        4. Unificar datos en un DataFrame.
        5. Limpiar columnas (tags como string, body sin saltos de línea).

    Retorna:
        pandas.DataFrame
    """

    urls = get_urls_Pacifista(sitemap_url, headers)

    if limit:
        urls = urls[:limit]

    data = []

    for url in urls:
        info = get_article_info_Pacifista(url, headers)
        if info:
            data.append(info)

    df = pd.DataFrame(data)

    # Normalización de columnas
    if "tags" in df.columns:
        df["tags"] = df["tags"].apply(
            lambda x: ", ".join(x) if isinstance(x, list) else ""
        )

    if "body" in df.columns:
        df["body"] = df["body"].apply(
            lambda x: x.replace("\n", " ") if isinstance(x, str) else ""
        )

    return df
