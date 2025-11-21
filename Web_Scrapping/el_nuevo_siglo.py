import requests
import pandas as pd
#from io import BytesIO
#import os

import xml.etree.ElementTree as ET
from urllib.parse import urljoin
from bs4 import BeautifulSoup
#import time
#import hashlib
from datetime import datetime
#import csv
import json

'''
Construimos las funciones del Scrapping
'''

def get_sitemap(url: str, headers: dict):
    """
    Obtiene y parsea un sitemap XML desde una URL.

    Recibe:
        url (str): URL del sitemap
        headers (dict): Headers para la petición HTTP

    Retorna:
        BeautifulSoup: Objeto parseado en formato XML
        o None si falla
    """
    try:
        resp = requests.get(url, headers=headers, timeout=10)

        if resp.status_code != 200:
            print(f"Error HTTP {resp.status_code} al acceder a {url}")
            return None

        try:
            soup = BeautifulSoup(resp.text, "xml")
            return soup
        except Exception as e:
            print(f"Error parseando XML: {e}")
            return None

    except Exception as e:
        print(f"Error al conectar con {url}: {e}")
        return None


def get_urls_sitemap(soup: BeautifulSoup):
    """
    Obtiene todas las URLs <loc> dentro de un sitemap XML.

    Recibe:
        soup (BeautifulSoup): Objeto XML parseado

    Retorna:
        list[str]: Lista de URLs encontradas, o None si falla.
    """

    if soup is None:
        print("Error: soup es None. No se puede extraer URLs.")
        return None

    try:
        urls = [loc.get_text(strip=True) for loc in soup.find_all("loc")]

        # Evitar devolver listas vacías
        if not urls:
            print("Advertencia: No se encontraron <loc> en el sitemap.")
            return []

        return urls

    except Exception as e:
        print(f"Error al obtener URLs del sitemap: {e}")
        return None


def get_article_info(url: str, headers: dict):
    """
    Descarga un artículo de El Nuevo Siglo y extrae:
    - título
    - subtítulo (None si no existe)
    - cuerpo (solo de div.field--name-field-free-text)
    - fecha
    - autor
    - imagen
    - sección (si aplica)
    - tags (None si no existen)
    """

    try:
        resp = requests.get(url=url, headers=headers)
        if resp.status_code != 200:
            print(f"Error {resp.status_code} al acceder a {url}")
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        # ---------- TÍTULO ----------
        title_tag = soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else None

        # ---------- SUBTÍTULO ----------
        subtitle_tag = None
        article_main = soup.find("div", class_="field--name-field-free-text")
        if article_main:
            # Buscar solo h2 o h3 dentro del artículo
            subtitle_tag = article_main.find(["h2","h3"])
        subtitle = subtitle_tag.get_text(strip=True) if subtitle_tag else None

        # ---------- CUERPO ----------
        if article_main:
            parrafos = article_main.find_all("p")
            body = "\n\n".join([p.get_text(strip=True) for p in parrafos]) if parrafos else None
        else:
            body = None

        # ---------- JSON-LD (fecha, autor, imagen) ----------
        date_published = None
        author = None
        image = None
        json_ld_tag = soup.find("script", type="application/ld+json")
        if json_ld_tag:
            try:
                data = json.loads(json_ld_tag.string)
                article_data = data["@graph"][0] if "@graph" in data else data
                date_published = article_data.get("datePublished")
                if "author" in article_data:
                    author = article_data["author"].get("name")
                if "image" in article_data:
                    image = article_data["image"].get("url")
            except:
                pass

        # ---------- TAGS ----------
        tag_container = soup.find_all("a", rel="tag")
        tags = [t.get_text(strip=True) for t in tag_container] if tag_container else None

        # ---------- SECCIÓN ----------
        section = "politica"  # como ya filtramos por política

        return {
            "url": url,
            "title": title,
            "subtitle": subtitle,
            "body": body,
            "date_published": date_published,
            "author": author,
            "image": image,
            "section": section,
            "tags": tags,
        }

    except Exception as e:
        print(f"Error procesando {url}: {e}")
        return None

    


'''
Construimos la función main
'''

def get_news_ElNuevoSiglo(
    sitemap_urls: list,
    headers: dict,
    section_filter: str = "politica",
    limit: int = None
    ):
    """
    Procesa noticias de El Nuevo Siglo desde una lista de sitemaps
    y devuelve un DataFrame limpio listo para guardar.

    ```
    Parámetros
    ----------
    sitemap_urls : list[str]
        Lista de URLs de sitemaps XML.
    headers : dict
        Headers HTTP.
    section_filter : str
        Palabra clave para filtrar por sección (en la URL).
    limit : int
        Número máximo de artículos a procesar (opcional).

    Retorna
    -------
    pandas.DataFrame
        DataFrame con la información de los artículos, con columnas:
        url, title, subtitle, body, date_published, author, image, section, tags.
        Listas convertidas a strings y saltos de línea reemplazados.
    """

    all_article_urls = []

    # Obtener todas las URLs de los sitemaps
    for sm_url in sitemap_urls:
        soup = get_sitemap(sm_url, headers)
        if soup:
            urls = get_urls_sitemap(soup)
            if urls:
                all_article_urls.extend(urls)

    # Filtrar URLs por sección
    filtered_urls = [
        u for u in all_article_urls 
        if section_filter.lower() in u.lower()
    ]

    if limit:
        filtered_urls = filtered_urls[:limit]

    data = []
    for url in filtered_urls:
        info = get_article_info(url, headers)
        if info:
            data.append(info)

    # Crear DataFrame
    df = pd.DataFrame(data)

    # Preprocesamiento para CSV
    if 'tags' in df.columns:
        df['tags'] = df['tags'].apply(lambda x: ", ".join(x) if isinstance(x, list) else "")

    if 'body' in df.columns:
        df['body'] = df['body'].apply(lambda x: x.replace("\n", " ") if isinstance(x, str) else "")

    return df
