import pandas as pd
import os
from el_nuevo_siglo import get_news_ElNuevoSiglo
from semana import get_news_Semana
from lafm import get_news_LaFM
from lavoragine import get_news_LaVoragine
from cerosetenta import get_news_CeroSetenta
from semanariovoz import get_news_SemanarioVoz
from cuestionpublica import get_news_CuestionPublica
import json
from dotenv import load_dotenv

load_dotenv()

'''
Leemos las varibles de entorno
'''

headers = json.loads(os.getenv("HEADER"))

## El Nuevo Siglo

nuevo_siglo = os.getenv('URL_EL_NUEVO_SIGLO')

sitemaps = ['https://www.elnuevosiglo.com.co/sitemap.xml?page=1',
            'https://www.elnuevosiglo.com.co/sitemap.xml?page=2' ]

sitemaps_Semana = ['https://www.semana.com/arc/outboundfeeds/sitemap/?outputType=xml',
 'https://www.semana.com/arc/outboundfeeds/sitemap/?outputType=xml&from=100',
 'https://www.semana.com/arc/outboundfeeds/sitemap/?outputType=xml&from=200']

url_LaFM = 'https://www.lafm.com.co/politica'

url_CuestionPublica = "https://cuestionpublica.com/sitemap_index.xml"
#df = get_news_ElNuevoSiglo(sitemap_urls=sitemaps, headers=headers, limit=5)

#df.to_csv("elnuevosiglo_politica.csv", index=False, encoding="utf-8")

#df = get_news_Semana(sitemap_urls=sitemaps_Semana, headers=headers, limit=5)
#df.to_csv("semana.csv", index=False, encoding="utf-8")

#df = get_news_LaFM(url_base=url_LaFM, headers=headers, limit=5)
#df.to_csv("lafm.csv", index=False, encoding="utf-8")

#df = get_news_LaVoragine("https://voragine.co/post-sitemap.xml", headers, limit=5)
#df.to_csv("lavoragine#.csv", index=False, encoding="utf-8")

df = get_news_CeroSetenta("https://cerosetenta.uniandes.edu.co/tema/politica/", headers, limit=5)
df.to_csv("cerosetenta.csv", index=False, encoding="utf-8")

#df = get_news_SemanarioVoz("https://semanariovoz.com/category/politica/", headers, limit=5)
#df.to_csv("semanariovoz.csv", index=False, encoding="utf-8")

#df = get_news_CuestionPublica(sitemap_index_url=url_CuestionPublica, headers=headers, limit=5)
#df.to_csv("cuestionpublica.csv", index=False, encoding="utf-8")

