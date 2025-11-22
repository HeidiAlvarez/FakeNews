import requests
import pandas as pd
from bs4 import BeautifulSoup

def get_urls_politica_CeroSetenta(url_base: str, headers: dict):
    """
    Obtiene todas las URLs de noticias de política de CeroSetenta desde la página de política.
    """
    resp = requests.get(url_base, headers=headers)
    if resp.status_code != 200:
        print(f"Error HTTP {resp.status_code} al acceder a {url_base}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    # Extraer todos los <a> que tengan <h2> dentro (títulos de artículos)
    urls = []
    for h2 in soup.find_all("h2"):
        a = h2.find_parent("a")
        if a and a["href"].startswith("https://cerosetenta.uniandes.edu.co/"):
            urls.append(a["href"])

    # Quitar duplicados
    urls = list(dict.fromkeys(urls))
    return urls


def get_article_info_CeroSetenta(url: str):
    """
    Descarga un artículo de CeroSetenta y extrae:
    title, body, date_published, author, section, tags.
    """
    resp = requests.get(url)
    if resp.status_code != 200:
        print(f"Error {resp.status_code} al acceder a {url}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # Título
    title_tag = soup.find("h1", class_="entry-title")
    title = title_tag.get_text(" ", strip=True) if title_tag else None

    # Autor
    autor_box = soup.find("div", class_="autor")
    author_tag = autor_box.find("a") if autor_box else None
    author = author_tag.get_text(strip=True) if author_tag else None

    # Fecha
    fecha_tag = autor_box.find("span") if autor_box else None
    date_published = fecha_tag.get_text(strip=True) if fecha_tag else None

    # Cuerpo
    body_container = soup.find("div", class_="entry-content")
    if body_container:
        parrafos = [p.get_text(strip=True) for p in body_container.find_all("p")]
        body = "\n\n".join(parrafos) if parrafos else None
    else:
        body = None

    # Tags (excluyendo política)
    tags_container = soup.find("div", class_="categorias_bottom") or soup.find("div", class_="categorias_top")
    tags = None
    if tags_container:
        tags = [
            a.get_text(strip=True)
            for a in tags_container.find_all("a")
            if not a.get("href", "").endswith("/politica/")
        ]

    # Sección fija
    section = "politica"

    return {
        "url": url,
        "title": title,
        "body": body,
        "date_published": date_published,
        "author": author,
        "section": section,
        "tags": tags,
    }


def get_news_CeroSetenta(url_base: str, headers: dict, limit: int = None):
    """
    Obtiene un DataFrame con los artículos de política de CeroSetenta.
    """
    urls = get_urls_politica_CeroSetenta(url_base, headers)

    if limit:
        urls = urls[:limit]

    data = []
    for url in urls:
        info = get_article_info_CeroSetenta(url)
        if info:
            data.append(info)

    df = pd.DataFrame(data)

    # Limpieza
    if "tags" in df.columns:
        df["tags"] = df["tags"].apply(lambda x: ", ".join(x) if isinstance(x, list) else "")

    if "body" in df.columns:
        df["body"] = df["body"].apply(lambda x: x.replace("\n", " ") if isinstance(x, str) else "")

    return df
