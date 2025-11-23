import requests
import pandas as pd
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()

url_CuestionPublica_loc     = os.getenv('URL_CUESTIONPUBLICA_LOC')
url_CuestionPublica_sitemap = os.getenv('URL_CUESTIONPUBLICA_SITEMAP')
url_CuestionPublica_url     = os.getenv('URL_CUESTIONPUBLICA_URL')

def get_urls_politica_CuestionPublica(sitemap_index_url: str, headers: dict):
    """
    Lee el sitemap_index, filtra los sitemaps que contienen posts,
    y devuelve todas las URLs de artículos.
    """

    resp = requests.get(sitemap_index_url, headers=headers)
    if resp.status_code != 200:
        print(f"Error HTTP {resp.status_code} al acceder al sitemap index.")
        return []

    root = ET.fromstring(resp.content)

    # Extraer URLs de cada sitemap
    sitemap_urls = [
        sm.find(url_CuestionPublica_loc).text
        for sm in root.findall(url_CuestionPublica_sitemap)
    ]

    # Filtrar solo los sitemaps relevantes
    post_sitemaps = [
        u for u in sitemap_urls
        if "post" in u.lower() or "cuestion" in u.lower()
    ]

    urls_finales = []

    # Procesar cada sitemap de posts
    for sm_url in post_sitemaps:
        resp2 = requests.get(sm_url, headers=headers)
        if resp2.status_code != 200:
            continue

        post_root = ET.fromstring(resp2.content)

        urls = [
            url_tag.find(url_CuestionPublica_loc).text
            for url_tag in post_root.findall(url_CuestionPublica_url)
        ]

        urls_finales.extend(urls)

    # quitar duplicados
    urls_finales = list(dict.fromkeys(urls_finales))

    return urls_finales


def get_article_info_CuestionPublica(url: str, headers: dict):
    """
    Descarga y parsea una noticia de Cuestión Pública,
    con los campos: title, subtitle, date_published, body, author, section, tags.
    """

    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print(f"Error HTTP {resp.status_code} en {url}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # -------------------------
    # TÍTULO
    # -------------------------
    titulo_tag = soup.find("h1")
    title = titulo_tag.get_text(strip=True) if titulo_tag else None

    # -------------------------
    # FECHA (primer meta:published_time)
    # -------------------------
    meta_fecha = soup.find("meta", {"property": "article:published_time"})
    date_published = meta_fecha.get("content") if meta_fecha else None

    # -------------------------
    # AUTOR
    # -------------------------
    meta_author = soup.find("meta", {"name": "author"})
    if meta_author:
        author = [meta_author.get("content")]
    else:
        author = None

    # -------------------------
    # SUBTÍTULO
    # Puede estar en <section class="entry-summary"> o similar
    # -------------------------
    subtitle_tag = (
        soup.find("section", class_="entry-summary")
        or soup.find("div", class_="subtitle")
        or soup.find("h2")
    )
    subtitle = subtitle_tag.get_text(strip=True) if subtitle_tag else None

    # -------------------------
    # CUERPO
    # -------------------------
    body_div = soup.find("div", class_="entry-content")
    if not body_div:
        body_div = soup.find("article")

    if body_div:
        paragraphs = [
            p.get_text(" ", strip=True)
            for p in body_div.find_all("p")
            if p.get_text(strip=True)
        ]
        body = "\n".join(paragraphs) if paragraphs else None
    else:
        body = None

    # -------------------------
    # TAGS
    # puede estar en <div class="tags"> o <ul>
    # -------------------------
    tags_div = soup.find("div", class_="tags")
    if tags_div:
        tags = [a.get_text(strip=True) for a in tags_div.find_all("a")]
    else:
        tags = None

    # -------------------------
    # SECCIÓN FIJA
    # -------------------------
    section = "politica"

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


def get_news_CuestionPublica(sitemap_index_url: str, headers: dict, limit: int = None):
    """
    Obtiene varias noticias desde Cuestión Pública usando el sitemap,
    las parsea y regresa un DataFrame.
    """

    urls = get_urls_politica_CuestionPublica(sitemap_index_url, headers)

    if limit:
        urls = urls[:limit]

    data = []

    for u in urls:
        info = get_article_info_CuestionPublica(u, headers)
        if info:
            data.append(info)

    df = pd.DataFrame(data)

    # -------------------------
    # Limpieza
    # -------------------------
    if "tags" in df.columns:
        df["tags"] = df["tags"].apply(
            lambda x: ", ".join(x) if isinstance(x, list) else None
        )

    if "body" in df.columns:
        df["body"] = df["body"].apply(
            lambda x: x.replace("\n", " ") if isinstance(x, str) else None
        )

    return df
