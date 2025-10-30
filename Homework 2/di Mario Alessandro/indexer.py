import time
import os
from elasticsearch import Elasticsearch, helpers
from config import INDEX_NAME, ELASTIC_HOST, MAPPING, DOCS_DIR

def create_index_and_mapping(es_client):
    try:
        es_client.indices.delete(index=INDEX_NAME, ignore=[400, 404])
        es_client.indices.create(index=INDEX_NAME, body=MAPPING)
        return True
    except Exception as e:
        print(f"ERRORE nella gestione dell'indice: {e}")
        return False

def generate_documents(directory):
    documents = []
    if not os.path.exists(directory):
        return []
        
    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            file_path = os.path.join(directory, filename) 
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                documents.append({
                    "_index": INDEX_NAME,
                    "_id": filename, 
                    "_source": {"nome_file": filename, "contenuto_file": content}
                })
            except Exception:
                pass 
    return documents

def index_files(es_client):
    start_time = time.time()
    docs_to_index = generate_documents(DOCS_DIR)
    
    if not docs_to_index: 
        print(f"ATTENZIONE: Nessun file trovato in {DOCS_DIR}.")
        return 0, 0.0
    
    successes, _ = helpers.bulk(es_client, docs_to_index, raise_on_error=False)
    end_time = time.time()
    es_client.indices.refresh(index=INDEX_NAME)
    
    return successes, end_time - start_time

def initialize_indexing():
    try:
        es = Elasticsearch(ELASTIC_HOST)
        if not es.ping(): raise ConnectionError()
        
        if not create_index_and_mapping(es): return None 

        num_files, duration = index_files(es)
        
        print(f"Indicizzazione completata in {duration:.4f} secondi. File indicizzati: {num_files}")
        return es
    except ConnectionError:
        print(f"ERRORE: Connessione a Elasticsearch fallita su {ELASTIC_HOST}.")
        return None
    except Exception as e:
        print(f"ERRORE durante l'indicizzazione: {e}")
        return None