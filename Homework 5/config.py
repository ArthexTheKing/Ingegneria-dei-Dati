from elasticsearch import Elasticsearch
from dotenv import load_dotenv
import os

load_dotenv()
PUBMED_EMAIL = os.getenv("PUBMED_EMAIL")

# Elasticsearch
ES_HOST = "http://localhost:9200"

INDEX_CONTENT_NAME = "content_index"
INDEX_TABLES_NAME = "tables_index"
INDEX_FIGURES_NAME = "figures_index"

# Percorsi
OUTPUT_DIR_ARXIV = "articles_arxiv"
METADATA_CSV_ARXIV = "_metadata_arxiv.csv"

OUTPUT_DIR_PUBMED = "articles_pubmed"
METADATA_CSV_PUBMED = "_metadata_pubmed.csv"


# Ricerca
SEARCH_QUERY_ARXIV = "text to speech"
SEARCH_QUERY_PUBMED =   "(((ultra-processed[Title] AND foods[Title]) OR (ultra-processed[Abstract] AND foods[Abstract])) OR " \
                        "((cardiovascular[Title] AND risk[Title]) OR (cardiovascular[Abstract] AND risk[Abstract]))) AND " \
                        "open access[filter]"
USERAGENT_ARXIV = "Mozilla/5.0"
USERAGENT_PUBMED = f"UniProject_DataEngineering_CorpusBuilder/1.0 (academic research; contact: {PUBMED_EMAIL})"
MAX_DOCS = 10

# Algoritmi
TFIDF_THRESHOLD = 0.15

def inizialize_es():
    es = Elasticsearch(ES_HOST)
    try:
        if not es.ping():
            raise ConnectionError(f"Impossibile connettersi a {ES_HOST}")
        return es
    except Exception as e:
        print(f"Errore Critico: {e}")
        return
    
def clean_text(text):
    """Pulisce il testo da spazi multipli."""
    return " ".join(text.split())