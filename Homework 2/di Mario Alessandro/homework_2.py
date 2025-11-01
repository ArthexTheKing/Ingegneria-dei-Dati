import os
import time
from elasticsearch import Elasticsearch, helpers

INDEX_NAME = "deep_file_index"

# Directory contenente i file
DOCS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dataset")

# Connessione a Elasticsearch
es = Elasticsearch("http://localhost:9200")

def create_index():
    if es.indices.exists(index=INDEX_NAME):
        print('Indice gia esistente, ricreazione dell\'indice')
        es.indices.delete(index=INDEX_NAME)

    settings = {
        "settings": {
            "analysis": {
                "analyzer": {
                    "custom_analyzer_nome": {"type": "simple"},
                    "custom_analyzer_contenuto": {"type": "standard", "stopwords": "_italian_"}
                }
            }
        },
        "mappings": {
            "properties": {
                "nome": {"type": "text", "analyzer": "custom_analyzer_nome"},
                "contenuto": {"type": "text", "analyzer": "custom_analyzer_contenuto"}
            }
        }
    }

    es.indices.create(index=INDEX_NAME, body=settings)
    print("Indice creato")


def index_files():
    start_time = time.time()
    txt_files = [f for f in os.listdir(DOCS_DIR) if f.endswith(".txt")]

    actions = []
    for file in txt_files:
        file_path = os.path.join(DOCS_DIR, file)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        actions.append({
            "_index": INDEX_NAME,
            "_source": {
                "nome": file,
                "contenuto": content
            }
        })

    helpers.bulk(es, actions)
    end_time = time.time()
    print(f"Indicizzati {len(actions)} file in {end_time-start_time}s")


def search_query(query_string):
    if query_string.startswith("nome:"):
        field = "nome"
        terms = query_string.replace("nome:", "").strip()
    elif query_string.startswith("contenuto:"):
        field = "contenuto"
        terms = query_string.replace("contenuto:", "").strip()
    else:
        print("Formato query non valido (usa: nome:... oppure contenuto:...)")
        return

    if terms.startswith('"') and terms.endswith('"'):
        search_body = {"query": {"match_phrase": {field: terms.strip('"')}}}
    else:
        search_body = {"query": {"match": {field: terms}}}

    results = es.search(index=INDEX_NAME, body=search_body)

    print("\nRisultati:")
    for hit in results["hits"]["hits"]:
        print(f"- {hit['_source']['nome']}")
    print()


if __name__ == "__main__":
    create_index()
    index_files()

    print("\nEsempi di query:")
    print("  nome:rete")
    print('  contenuto:"apprendimento profondo"\n')

    while True:
        q = input("Query > ")
        if q.lower() in ["exit", "quit"]:
            break
        search_query(q)
