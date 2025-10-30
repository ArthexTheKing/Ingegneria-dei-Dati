from indexer import initialize_indexing
from searcher import main_searcher

if __name__ == "__main__":
    # 1. Indicizzazione
    es_client = initialize_indexing() 
    
    # 2. Avvio del motore di ricerca
    if es_client:
        main_searcher(es_client)