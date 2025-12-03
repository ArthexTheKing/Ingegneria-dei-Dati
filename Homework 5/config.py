from elasticsearch import Elasticsearch

# Elasticsearch
ES_HOST = "http://localhost:9200"

INDEX_CONTENT_NAME = "arxiv_index"
INDEX_TABLES_NAME = "arxiv_tables"
INDEX_FIGURES_NAME = "arxiv_figures"

# Percorsi
OUTPUT_DIR = "articles_arxiv"
METADATA_CSV = "_metadata.csv"

# Ricerca
SEARCH_QUERY = "text to speech"
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