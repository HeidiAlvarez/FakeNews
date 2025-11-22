import requests
import pandas as pd
from bs4 import BeautifulSoup


def get_urls_politica_LaFM(url_base: str, headers: dict):
    """
    Obtiene todas las URLs de noticias de política de La FM desde la página principal.
    """
    resp = requests.get(url_base, headers=headers)
    if resp.status_code != 200:
        print(f"Error HTTP {resp.status_code} al acceder a {url_base}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    links = soup.find_all("a", href=True)

    urls = []
    for a in links:
        href = a["href"]
        if href.startswith("/politica/"):
            urls.append("https://www.lafm.com.co" + href)

    # Quitar duplicados
    urls = list(dict.fromkeys(urls))
    return urls


def get_article_info_LaFM(url: str, headers: dict):
    """
    Descarga un artículo de La FM y extrae:
    title, subtitle, body, date_published, author, section, tags.
    """
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print(f"Error {resp.status_code} al acceder a {url}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # Título
    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else None

    # Subtítulo (no existe)
    subtitle = None

    # Autor
    autor_box = soup.find("div", class_="author")
    author = autor_box.get_text(strip=True) if autor_box else None

    # Fecha
    fecha_tag = soup.find("meta", {"property": "article:published_time"})
    date_published = fecha_tag["content"] if fecha_tag else None

    # Tags
    tags_container = soup.find("div", class_="tags")
    tags = [a.get_text(strip=True) for a in tags_container.find_all("a")] if tags_container else None

    # Cuerpo
    body_container = soup.find("article", class_="news-content")
    if body_container:
        parrafos = [p.get_text(strip=True) for p in body_container.find_all("p")]
        body = "\n\n".join(parrafos) if parrafos else None
    else:
        body = None

    # Sección fija
    section = "politica"

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


def get_news_LaFM(url_base: str, headers: dict, limit: int = None):
    """
    Obtiene un DataFrame con los artículos de política de La FM.
    """
    urls = get_urls_politica_LaFM(url_base, headers)

    if limit:
        urls = urls[:limit]

    data = []
    for url in urls:
        info = get_article_info_LaFM(url, headers)
        if info:
            data.append(info)

    df = pd.DataFrame(data)

    # Limpieza
    if "tags" in df.columns:
        df["tags"] = df["tags"].apply(lambda x: ", ".join(x) if isinstance(x, list) else "")

    if "body" in df.columns:
        df["body"] = df["body"].apply(lambda x: x.replace("\n", " ") if isinstance(x, str) else "")

    return df
