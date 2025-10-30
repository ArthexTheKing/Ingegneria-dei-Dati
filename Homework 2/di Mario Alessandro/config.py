import os

# --- CONFIGURAZIONE ESECUZIONE ---
INDEX_NAME = "deep_learning_index"
ELASTIC_HOST = "http://localhost:9200"
DOCS_FOLDER_NAME = "dataset" 

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(BASE_DIR, DOCS_FOLDER_NAME)

# --- MAPPING FINALE STABILE ---
MAPPING = {
    "mappings": {
        "properties": {
            "nome_file": {"type": "keyword" },
            "contenuto_file": {"type": "text", "analyzer": "italian"}
        }
    }
}