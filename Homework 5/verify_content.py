from config import INDEX_CONTENT_NAME, inizialize_es

def verify_index_content():

    es = inizialize_es()

    # Controllo conteggio totale
    count = es.count(index=INDEX_CONTENT_NAME)['count']
    print(f"Totale contenuti nell'indice '{INDEX_CONTENT_NAME}': {count}")
    
    # Recupero di un documento a caso (usiamo una query match_all con size 1)
    resp = es.search(index=INDEX_CONTENT_NAME, body={"query": {"match_all": {}}, "size": 1})
    
    if not resp['hits']['hits']:
        print("Indice vuoto.")
        return

    doc = resp['hits']['hits'][0]['_source']
    full_text = doc.get('full_text', "")
    title = doc.get('title', "")

    print(f"\nTitolo: {title}")

    # Mostra il contenuto salvato
    print("\nContenuto Salvato (Anteprima):")
    print(" ".join(full_text[:300].split()) + "...")


if __name__ == "__main__":
    verify_index_content()