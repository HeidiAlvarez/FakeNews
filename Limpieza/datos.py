import os
import time
import json
import pandas as pd
import requests
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

# Importación de tus funciones individuales
from el_nuevo_siglo import get_news_ElNuevoSiglo
#from semana import get_news_Semana
from lafm import get_news_LaFM
from lavoragine import get_news_LaVoragine
from cerosetenta import get_news_CeroSetenta
from semanariovoz import get_news_SemanarioVoz
from cuestionpublica import get_news_CuestionPublica
from elpacifista import get_news_Pacifista
from lasillavacia import get_news_LaSilla


load_dotenv()


# ===============================
#     Configuración Global
# ===============================

HEADERS = json.loads(os.getenv("HEADER"))

SITEMAPS = {
    "ElNuevoSiglo": {
        "func": get_news_ElNuevoSiglo,
        "args": {"sitemap_urls": [
            "https://www.elnuevosiglo.com.co/sitemap.xml?page=1",
            "https://www.elnuevosiglo.com.co/sitemap.xml?page=2"
        ]},
        "espectro": "derecha"
    },

    "LaFM": {
        "func": get_news_LaFM,
        "args": {"url_base": "https://www.lafm.com.co/politica"},
        "espectro": "derecha"
    },

    "LaVoragine": {
        "func": get_news_LaVoragine,
        "args": {"sitemap_url": "https://voragine.co/post-sitemap.xml"},
        "espectro": "izquierda"
    },

    "CeroSetenta": {
        "func": get_news_CeroSetenta,
        "args": {"url_base": "https://cerosetenta.uniandes.edu.co/tema/politica/"},
        "espectro": "izquierda"
    },

    "SemanarioVoz": {
        "func": get_news_SemanarioVoz,
        "args": {"url_base": "https://semanariovoz.com/category/politica/"},
        "espectro": "izquierda"
    },

    "CuestionPublica": {
        "func": get_news_CuestionPublica,
        "args": {"sitemap_index_url": "https://cuestionpublica.com/sitemap_index.xml"},
        "espectro": "centro"
    },

    "Pacifista": {
        "func": get_news_Pacifista,
        "args": {"sitemap_url": "https://pacifista.tv/post-sitemap.xml"},
        "espectro": "centro"
    },

    "LaSillaVacia": {
        "func": get_news_LaSilla,
        "args": {"sitemap_index_url": "https://www.lasillavacia.com/sitemap_index.xml"},
        "espectro": "centro"
    },
}

def run_with_retry(func, kwargs, limit, retries=3, sleep_base=2):
    """
    Ejecuta una función con reintentos.

    Args:
        func (callable): función de scraping del medio.
        kwargs (dict): argumentos base del medio.
        limit (int): límite de artículos.
        retries (int): reintentos.
        sleep_base (int): espera creciente exponencial.

    Returns:
        pd.DataFrame o None
    """
    for i in range(retries):
        try:
            print(f"Intentando {func.__name__}, intento {i+1}/{retries}")
            df = func(limit=limit, headers=HEADERS, **kwargs)
            return df
        except Exception as e:
            print(f"Error en {func.__name__}: {e}")
            time.sleep(sleep_base * (i+1))

    print(f"❌ Falló definitivamente: {func.__name__}")
    return None



def get_all_news(limit=200, workers=5):
    """
    Ejecuta scraping de todos los medios definidos en SITEMAPS.

    Args:
        limit (int): límite de artículos por medio.
        workers (int): número de hilos en paralelo.

    Returns:
        pd.DataFrame: dataframe consolidado con:
            - url
            - title
            - subtitle
            - date_published
            - body
            - author
            - section
            - tags
            - medio
            - espectro_politico
    """

    tasks = []
    final_dataframes = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        for medio, config in SITEMAPS.items():
            func = config["func"]
            kwargs = config["args"]
            espectro = config["espectro"]

            future = executor.submit(run_with_retry, func, kwargs, limit)
            tasks.append((medio, espectro, future))

        for medio, espectro, future in tasks:
            df = future.result()
            if df is not None and not df.empty:
                df["medio"] = medio
                df["espectro_politico"] = espectro
                final_dataframes.append(df)
            else:
                print(f"⚠️ {medio} no devolvió datos.")

    if not final_dataframes:
        print("❌ No se obtuvo ningún dataframe.")
        return pd.DataFrame()

    df_final = pd.concat(final_dataframes, ignore_index=True)
    return df_final


if __name__ == "__main__":
    df = get_all_news(limit=300, workers=6)
    df.to_csv("noticias_consolidadas.csv", index=False, encoding="utf-8")
    print("Archivo generado: noticias_consolidadas.csv")
