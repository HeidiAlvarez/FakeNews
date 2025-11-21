import requests
import pandas as pd
from bs4 import BeautifulSoup
import json


def get_sitemap(url: str, headers: dict):
    """Obtiene y parsea un sitemap XML desde una URL."""
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
    """Obtiene todas las URLs <loc> dentro de un sitemap XML."""
    if soup is None:
        print("Error: soup es None. No se puede extraer URLs.")
        return None
    try:
        urls = [loc.get_text(strip=True) for loc in soup.find_all("loc")]
        if not urls:
            print("Advertencia: No se encontraron <loc> en el sitemap.")
            return []
        return urls
    except Exception as e:
        print(f"Error al obtener URLs del sitemap: {e}")
        return None


def get_article_info(url: str, headers: dict):
    """
    Descarga un artículo de Semana y extrae:
    - título
    - subtítulo (None si no existe)
    - cuerpo
    - fecha
    - autor
    - sección
    - tags
    """
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            print(f"Error {resp.status_code} al acceder a {url}")
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        title = subtitle = body = date_published = author = section = tags = None

        json_ld_tags = soup.find_all("script", type="application/ld+json")
        for tag in json_ld_tags:
            try:
                data = json.loads(tag.string)
            except:
                continue

            if data.get("@type") == "NewsArticle" and "articleBody" in data:
                title = data.get("headline")
                date_published = data.get("datePublished")
                author = data.get("author", {}).get("name")
                body = data.get("articleBody")
                section = data.get("articleSection")
                tags = data.get("keywords")
                break

        subtitle = None

        return {
            "url": url,
            "title": title,
            "subtitle": subtitle,
            "body": body,
            "date_published": date_published,
            "author": author,
            "section": section,
            "tags": tags,
        }

    except Exception as e:
        print(f"Error procesando {url}: {e}")
        return None


def get_news_Semana(sitemap_urls: list, headers: dict, section_filter: str = "politica", limit: int = None):
    """
    Procesa noticias de Semana desde una lista de sitemaps
    y devuelve un DataFrame limpio listo para usar.
    """
    all_article_urls = []

    for sm_url in sitemap_urls:
        soup = get_sitemap(sm_url, headers)
        if soup:
            urls = get_urls_sitemap(soup)
            if urls:
                all_article_urls.extend(urls)

    filtered_urls = [u for u in all_article_urls if section_filter.lower() in u.lower()]
    if limit:
        filtered_urls = filtered_urls[:limit]

    data = []
    for url in filtered_urls:
        info = get_article_info(url, headers)
        if info:
            data.append(info)

    df = pd.DataFrame(data)

    if 'tags' in df.columns:
        df['tags'] = df['tags'].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)

    if 'body' in df.columns:
        df['body'] = df['body'].apply(lambda x: x.replace("\n", " ") if isinstance(x, str) else x)

    return df
