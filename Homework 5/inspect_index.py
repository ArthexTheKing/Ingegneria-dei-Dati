from elasticsearch import Elasticsearch

ES_HOST = "http://localhost:9200"
INDEX_NAME = "arxiv_index" 

def verify():
    es = Elasticsearch(ES_HOST)
    
    # Recupera 1 documento
    try:
        resp = es.search(index=INDEX_NAME, body={"query": {"match_all": {}}, "size": 1})
    except Exception as e:
        print(f"Errore ricerca: {e}")
        return
    
    if not resp['hits']['hits']:
        print("Indice vuoto.")
        return

    doc = resp['hits']['hits'][0]['_source']
    full_text = doc.get('full_text', "")
    title = doc.get('title', "")

    print(f"Titolo: {title}")

    # Mostra il contenuto salvato
    print("\nContenuto Salvato (Anteprima):")
    print(" ".join(full_text[:300].split()) + "...")


if __name__ == "__main__":
    verify()