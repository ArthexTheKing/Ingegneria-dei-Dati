from elasticsearch import Elasticsearch
from indexer import setup_index
from retriever import fetch_and_index_documents

ES_HOST = "http://localhost:9200"
INDEX_NAME = "arxiv_index"
SEARCH_QUERY = "text to speech"
MAX_DOCS = 10
OUTPUT_DIR = "articles_arxiv"

def main():
    try:
        es = Elasticsearch(ES_HOST)
        if not es.ping():
            raise ConnectionError(f"Impossibile connettersi a {ES_HOST}")
        print(f"Connesso a Elasticsearch ({ES_HOST})")
    except Exception as e:
        print(f"Errore Critico: {e}")
        return

    # Setup (Cancella e ricrea indice)
    setup_index(es, INDEX_NAME)

    # Download, Pulizia e Indicizzazione
    fetch_and_index_documents(es, INDEX_NAME, SEARCH_QUERY, OUTPUT_DIR, MAX_DOCS)

if __name__ == "__main__":
    main()