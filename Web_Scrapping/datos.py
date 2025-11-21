import pandas as pd
import os
from el_nuevo_siglo import get_news_ElNuevoSiglo
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


#df = get_news_ElNuevoSiglo(sitemap_urls=sitemaps, headers=headers, limit=5)

#df.to_csv("elnuevosiglo_politica.csv", index=False, encoding="utf-8")
