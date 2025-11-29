import requests
import pandas as pd
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()

url_SemanarioVoz = os.getenv('URL_SEMANARIOVOZ')

def get_urls_politica_SemanarioVoz(url_base: str, headers: dict):
    """
    Obtiene todas las URLs de noticias de política desde la página de Semanario Voz.
    """
    resp = requests.get(url_base, headers=headers)

    if resp.status_code != 200:
        print(f"Error HTTP {resp.status_code} al acceder a {url_base}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    urls = []

    # Extraer URLs del módulo principal de artículos
    for module in soup.find_all("div", class_="td-module-container"):
        a = module.find("a", href=True)
        if a:
            href = a["href"]
            if href.startswith(url_SemanarioVoz):
                urls.append(href)

    # Quitar duplicados
    urls = list(dict.fromkeys(urls))
    return urls


def get_article_info_SemanarioVoz(url: str, headers: dict):
    """
    Descarga y parsea una noticia de Semanario Voz:
    title, subtitle, date_published, body, author(None), section, tags.
    """
    resp = requests.get(url, headers=headers)

    if resp.status_code != 200:
        print(f"Error HTTP {resp.status_code} al acceder a {url}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # -------------------------
    # TÍTULO
    # -------------------------
    titulo_tag = soup.select_one(".tdb-title-text")
    title = titulo_tag.get_text(strip=True) if titulo_tag else None

    # -------------------------
    # SUBTÍTULO
    # -------------------------
    subtitulo_tag = (
        soup.select_one("p.td-post-sub-title")
        or soup.select_one(".tdb-sub-title")
        or soup.select_one(".td-post-sub-title")
    )
    subtitle = subtitulo_tag.get_text(strip=True) if subtitulo_tag else None

    # -------------------------
    # FECHA
    # -------------------------
    fecha_tag = soup.select_one("time.entry-date")

    if fecha_tag:
        date_published = fecha_tag.get_text(strip=True)
    else:
        meta_date = soup.select_one('meta[property="article:published_time"]')
        date_published = meta_date["content"] if meta_date else None

    # -------------------------
    # CUERPO
    # -------------------------
    body_container = soup.select_one(".td-post-content")

    if body_container:
        parrafos = body_container.find_all("p")
        body = "\n".join(
            p.get_text(" ", strip=True) 
            for p in parrafos if p.get_text(strip=True)
        )
    else:
        body = None

    # -------------------------
    # TAGS
    # -------------------------
    tags_raw = (
        soup.select(".td-post-tags a")
        or soup.select("ul.td-tags a")
        or soup.select(".tdb-tags a")
    )

    tags = [t.get_text(strip=True) for t in tags_raw] if tags_raw else None

    # -------------------------
    # NO HAY AUTOR EN SEMANARIO VOZ
    # (si aparece en el futuro, se ajusta aquí)
    # -------------------------
    author = None

    # Sección fija
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


def get_news_SemanarioVoz(url_base: str, headers: dict, limit: int = None):
    """
    Descarga varias noticias de Semanario Voz (política) y retorna un DataFrame.
    """
    urls = get_urls_politica_SemanarioVoz(url_base, headers)

    if limit:
        urls = urls[:limit]

    data = []

    for url in urls:
        info = get_article_info_SemanarioVoz(url, headers)
        if info:
            data.append(info)

    df = pd.DataFrame(data)

    # Limpieza y uniformización
    if "tags" in df.columns:
        df["tags"] = df["tags"].apply(lambda x: ", ".join(x) if isinstance(x, list) else "")

    if "body" in df.columns:
        df["body"] = df["body"].apply(
            lambda x: x.replace("\n", " ") if isinstance(x, str) else ""
        )

    return df
