import requests
import pandas as pd
from bs4 import BeautifulSoup

def get_urls_politica_LaVoragine(sitemap_url: str, headers: dict = None):
    """
    Obtiene todas las URLs de noticias de política de La Vóragine desde el sitemap de posts.
    """

    resp = requests.get(sitemap_url, headers=headers)
    if resp.status_code != 200:
        print(f"Error HTTP {resp.status_code} al acceder a {sitemap_url}")
        return []

    soup = BeautifulSoup(resp.text, "xml")
    urls = [loc.get_text(strip=True) for loc in soup.find_all("loc") if "/politica/" in loc.get_text(strip=True)]

    # Quitar duplicados
    urls = list(dict.fromkeys(urls))
    return urls

def get_article_info_LaVoragine(url: str, headers: dict):
    """
    Descarga un artículo de La Vorágine y extrae:
    title, subtitle, body, date_published, author, section, tags.
    """
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print(f"Error {resp.status_code} al acceder a {url}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # ---------- Título ----------
    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else None

    # ---------- Subtítulo ----------
    subtitle_tag = soup.find("h2", class_="subtitle")
    subtitle = subtitle_tag.get_text(strip=True) if subtitle_tag else None

    # ---------- Autor ----------
    autor_meta = soup.find("meta", {"name": "author"})
    if autor_meta:
        author = autor_meta.get("content")
    else:
        autor_tag = soup.find("span", class_="author-name")  # ajuste si existe
        author = autor_tag.get_text(strip=True) if autor_tag else None

    # ---------- Fecha ----------
    fecha_tag = soup.find("meta", {"property": "article:published_time"})
    date_published = fecha_tag["content"] if fecha_tag else None

    # ---------- Sección ----------
    section = "politica"

    # ---------- Tags ----------
    tags_container = soup.find("div", class_="tags")
    tags = [a.get_text(strip=True) for a in tags_container.find_all("a")] if tags_container else None

    # ---------- Body ----------
    article_tag = soup.find("article")
    if article_tag:
        parrafos = [p.get_text(strip=True) for p in article_tag.find_all("p")]
        body = "\n\n".join(parrafos) if parrafos else None
    else:
        body = None

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


def get_news_LaVoragine(sitemap_url: str, headers: dict = None, limit: int = None):
    """
    Obtiene un DataFrame con los artículos de política de La Vóragine.
    """
    urls = get_urls_politica_LaVoragine(sitemap_url, headers=headers)


    if limit:
        urls = urls[:limit]

    data = []
    for url in urls:
        info = get_article_info_LaVoragine(url, headers=headers)
        if info:
            data.append(info)

    df = pd.DataFrame(data)

    # Limpieza
    if "tags" in df.columns:
        df["tags"] = df["tags"].apply(lambda x: ", ".join(x) if isinstance(x, list) else "")

    if "body" in df.columns:
        df["body"] = df["body"].apply(lambda x: x.replace("\n", " ") if isinstance(x, str) else "")

    return df
