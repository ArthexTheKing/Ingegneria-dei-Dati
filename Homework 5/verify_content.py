from config import INDEX_CONTENT_NAME, inizialize_es

def verify_index_content():

    es = inizialize_es()

    source_to_check = 'pubmed' # Cambia in 'arxiv' o 'pubmed' per verificare diverse sorgenti

    # Controllo conteggio totale
    count = es.count(index=INDEX_CONTENT_NAME)['count']
    print(f"Totale contenuti nell'indice '{INDEX_CONTENT_NAME}': {count}")

    query_arxiv = {"query": {"term": {"source": "arxiv"}}}
    count_arxiv = es.count(index=INDEX_CONTENT_NAME, body=query_arxiv)['count']
    print(f"Documenti con source='arxiv':  {count_arxiv}")

    query_pubmed = {"query": {"term": {"source": "pubmed"}}}
    count_pubmed = es.count(index=INDEX_CONTENT_NAME, body=query_pubmed)['count']
    print(f"Documenti con source='pubmed':  {count_pubmed}\n")

    
    # Recupero di un documento a caso (usiamo una query match_all con size 1)
    search_body = {
        "query": {
            "function_score": {
                "query": {"term": {"source": source_to_check}}, # Mantiene il filtro sulla sorgente
                "random_score": {}, # Assegna un punteggio casuale a ogni documento
                "boost_mode": "replace" # Sostituisce il punteggio originale con quello casuale
            }
        },
        "size": 1
    }
    resp = es.search(index=INDEX_CONTENT_NAME, body=search_body)
    
    if not resp['hits']['hits']:
        print("Indice vuoto.")
        return

    doc = resp['hits']['hits'][0]['_source']
    doc_id = resp['hits']['hits'][0]['_id']

    print(f"Source: {doc.get('source')}") # Source
    print(f"ID documento: {doc.get('document_id')}") # ID documento
    print(f"Titolo: {doc.get('title')}") # titolo
    print(f"Data: {doc.get('date')}") # data
    print(f"Autore: {doc.get('authors')}") # autori
    print(f"URL PDF: {doc.get('pdf_url')}") # URL PDF
    print(f"Path locale: {doc.get('local_file_saved')}") # Path locale
    print(f"ID documento in ES: {doc_id}") # ID in ES

    # Mostra l'abstract
    print("\nAbstract (Anteprima):")
    print(" ".join(doc.get('abstract')[:300].split()) + "...")

    # Mostra il contenuto salvato
    print("\nContenuto Salvato (Anteprima):")
    print(" ".join(doc.get('full_text')[:300].split()) + "...")


if __name__ == "__main__":
    verify_index_content()