import os
import time
from elasticsearch import Elasticsearch

# --- 1. CONFIGURAZIONE E SETUP ---

INDEX_NAME = "deep_learning_index"

# Definisce il percorso assoluto della directory dei documenti utilizzando os.path
DOCS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "documenti_deep_learning")

# Connessione a Elasticsearch
es = Elasticsearch('http://localhost:9200')

# Definizione del mapping
MAPPING = {
    "settings": {
        "analysis": {
            "analyzer": {
                "filename_analyzer": {
                    "tokenizer": "whitespace", 
                    "filter": ["lowercase", "italian_stop"]
                }
            },
            "filter": {
                "italian_stop": {
                    "type": "stop",
                    "stopwords": "_italian_"
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "nome": {"type": "text", "analyzer": "filename_analyzer"},
            "contenuto": {"type": "text", "analyzer": "italian"}
        }
    }
}

def create_index():
    """Crea l'indice, eliminando la versione precedente se esistente."""
    try:
        if es.indices.exists(index=INDEX_NAME):
            es.indices.delete(index=INDEX_NAME)
            print(f"Indice '{INDEX_NAME}' eliminato.")
        
        # L'indice viene creato con il nuovo mapping
        es.indices.create(index=INDEX_NAME, body=MAPPING)
        print(f"Indice '{INDEX_NAME}' creato con successo.")
    except Exception as e:
        print(f"Errore nella creazione dell'indice: {e}")
        raise

# --- 2. FUNZIONE DI INDICIZZAZIONE ---

def index_documents():
    """Indicizza i file .txt leggendoli dal percorso assoluto e calcola il tempo."""
    
    if not os.path.isdir(DOCS_DIR):
        print(f"ERRORE: La directory '{DOCS_DIR}' non esiste. Esegui prima 'genera_documenti.py'.")
        return 0, 0.0
    
    indexed_count = 0
    start_time = time.time()
    
    for filename in os.listdir(DOCS_DIR):
        if filename.endswith(".txt"):
            filepath = os.path.join(DOCS_DIR, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                document = {
                    "nome": filename,
                    "contenuto": content
                }
                
                es.index(index=INDEX_NAME, id=filename, document=document)
                indexed_count += 1
                
            except Exception as e:
                print(f"Errore durante l'indicizzazione di {filename}: {e}")

    end_time = time.time()
    indexing_time = end_time - start_time
    
    return indexed_count, indexing_time

# --- 3. FUNZIONE DI INTERROGAZIONE (Invariata) ---

def search_index():
    """Legge la query da console, interroga l'indice e stampa i risultati."""
    print("\n--- Console di Interrogazione ---")
    print("Sintassi: campo:termine1 termine2 ... (es: nome:reti neurali OR contenuto:black box)")
    print("Phrase Query: campo:\"parole esatte\" (es: contenuto:\"reti neurali ricorrenti\")")
    print("Digita 'esci' per terminare.")
    
    while True:
        try:
            user_input = input("Inserisci la query: ").strip()
            
            if user_input.lower() == 'esci':
                break

            search_body = {
                "query": {
                    "query_string": {
                        "query": user_input,
                        "default_operator": "AND" 
                    }
                }
            }
            
            res = es.search(index=INDEX_NAME, body=search_body)
            
            print(f"\nRisultati trovati: {res['hits']['total']['value']}")
            for hit in res['hits']['hits']:
                source = hit["_source"]
                print(f"  > Punteggio: {hit['_score']:.2f} - File: {source['nome']}")
                snippet = source['contenuto'][:100].replace('\n', ' ') + "..."
                print(f"    Contenuto: {snippet}")
            print("-" * 30)

        except Exception as e:
            print(f"Errore nella query o nella connessione: {e}")
            print("Verifica la sintassi della query o la connessione a Elasticsearch.")

# --- 4. ESECUZIONE PRINCIPALE ---

if __name__ == "__main__":
    try:
        create_index() 
        count, time_taken = index_documents()
        
        print(f"\n--- Riepilogo Indicizzazione ---")
        print(f"File indicizzati: {count}")
        print(f"Tempo di indicizzazione (sec): {time_taken:.4f}")
        
        if count > 0:
            search_index()
        
    except Exception as e:
        print(f"Errore critico: {e}")
        print("Assicurati che Elasticsearch sia in esecuzione e di aver eseguito 'genera_documenti.py'.")