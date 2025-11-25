import requests
import pandas as pd
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import os
from dotenv import load_dotenv

load_dotenv()

namespace = os.getenv('URL_ElPACIFISTA')



def get_urls_LaSilla(sitemap_index_url: str, headers: dict):
    """
    Descarga el sitemap_index.xml de La Silla Vacía y extrae todos los sitemaps.
    Luego descarga uno por uno y obtiene las URLs de artículos.

    Retorna:
        list[str]: lista de URLs limpias de artículos.
    """

    resp = requests.get(sitemap_index_url, headers=headers)
    if resp.status_code != 200:
        print(f"Error HTTP {resp.status_code} al acceder a {sitemap_index_url}")
        return []

    try:
        root = ET.fromstring(resp.content)
    except Exception as e:
        print("Error parseando XML:", e)
        return []

    # Namespace estándar
#   ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"

    # Extraer URLs de sitemaps
    sitemap_urls = [
        sm.find(f"{namespace}loc").text
        for sm in root.findall(f"{namespace}sitemap")
    ]

    all_urls = []

    for sm_url in sitemap_urls:
        resp_sm = requests.get(sm_url, headers=headers)
        if resp_sm.status_code != 200:
            continue

        try:
            root_sm = ET.fromstring(resp_sm.content)
        except Exception:
            continue

        urls = [
            tag.find(f"{namespace}loc").text
            for tag in root_sm.findall(f"{namespace}url")
        ]

        # Filtrar imágenes y basura
        clean = [
            u for u in urls
            if "/wp-content/" not in u.lower()
            and not u.lower().endswith((".jpg", ".png", ".jpeg", ".gif"))
        ]

        all_urls.extend(clean)

    return all_urls


def get_article_info_LaSilla(url: str, headers: dict):
    """
    Descarga y parsea un artículo de La Silla Vacía.

    Extrae:
        - title
        - subtitle
        - date_published
        - body
        - author
        - tags
        - section (siempre 'politica' o según URL)
    """

    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print(f"Error HTTP {resp.status_code} al acceder a {url}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # TÍTULO
    title_tag = (
        soup.select_one("h1.title")
        or soup.find("h1")
        or soup.title
    )
    title = title_tag.get_text(strip=True) if title_tag else None

    # SUBTÍTULO
    subtitle = None

    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and meta_desc.get("content"):
        subtitle = meta_desc["content"].strip()

    # FECHA
    date_published = None

    # 1) <meta property="article:published_time">
    meta_date = soup.find("meta", attrs={"property": "article:published_time"})
    if meta_date and meta_date.get("content"):
        date_published = meta_date["content"]

    # 2) <time datetime="...">
    if not date_published:
        time_tag = soup.find("time", attrs={"datetime": True})
        if time_tag:
            date_published = time_tag["datetime"]

    # AUTOR
    author = None

    # Ejemplo: <span class="article__author-name">Nombre</span>
    tag_author = soup.select_one(".article__author-name")
    if tag_author:
        author = tag_author.get_text(strip=True)

    # CUERPO
    body = None

    container = (
        soup.select_one(".entry-content")
        or soup.select_one(".article__body")
        or soup.find("article")
    )

    if container:
        paragraphs = [
            p.get_text(" ", strip=True)
            for p in container.find_all("p")
            if p.get_text(strip=True)
        ]
        body = "\n".join(paragraphs) if paragraphs else None

    # TAGS
    tags_container = soup.select_one("div.field--name-field-tags")
    if tags_container:
        tags = [
            a.get_text(strip=True)
            for a in tags_container.select("a")
        ]
    else:
        tags = None

    # SECCIÓN (se deduce del URL)
    section = "politica"
    
    # RETORNO
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

def get_news_LaSilla(sitemap_index_url: str, headers: dict, limit: int = None):
    """
    Descarga el sitemap general, obtiene URLs, filtra política,
    procesa cada artículo y retorna un DataFrame limpio.
    """

    urls = get_urls_LaSilla(sitemap_index_url, headers)

    # Filtrar política
    urls = [u for u in urls if "politica" in u.lower() and "/podcasts/" not in u.lower()]

    if limit:
        urls = urls[:limit]

    data = []

    for url in urls:
        info = get_article_info_LaSilla(url, headers)
        if info:
            data.append(info)

    df = pd.DataFrame(data)

    # Normalización igual al código de Pacifista
    if "tags" in df.columns:
        df["tags"] = df["tags"].apply(
            lambda x: ", ".join(x) if isinstance(x, list) else None
        )

    if "body" in df.columns:
        df["body"] = df["body"].apply(
            lambda x: x.replace("\n", " ") if isinstance(x, str) else None
        )

    return df
