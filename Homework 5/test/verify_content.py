# per eseguire: python -m test.verify_content

from src.core.es import get_es_client
from src.config import Config

def verify_content():

    # Connessione ES
    es = get_es_client()
    
    # Indici
    INDEX_DOCS = Config.INDEX_DOCS
    INDEX_TABLES = Config.INDEX_TABLES
    INDEX_FIGURES = Config.INDEX_FIGURES

    source_to_check = 'arxiv'  # 'arxiv' o 'pubmed'
    NUM_DOCS_TO_SHOW = 2 

    # Statistiche generali
    print("\nStatistiche Indice Documenti")
    
    # Controllo esistenza
    if not es.indices.exists(index=INDEX_DOCS):
        print(f"L'indice '{INDEX_DOCS}' non esiste.")
        return

    # Conteggi totali
    count = es.count(index=INDEX_DOCS)['count']
    print(f"Totale documenti in '{INDEX_DOCS}': {count}")

    query_arxiv = {"query": {"term": {"source": "arxiv"}}}
    count_arxiv = es.count(index=INDEX_DOCS, body=query_arxiv)['count']
    print(f"Documenti ArXiv:  {count_arxiv}")

    query_pubmed = {"query": {"term": {"source": "pubmed"}}}
    count_pubmed = es.count(index=INDEX_DOCS, body=query_pubmed)['count']
    print(f"Documenti PubMed: {count_pubmed}")
    
    # Recupero documenti
    print(f"Recupero {NUM_DOCS_TO_SHOW} documenti con source='{source_to_check}'")

    search_body = {
        "query": {
            "function_score": {
                "query": {"term": {"source": source_to_check}}, 
                "random_score": {}, 
                "boost_mode": "replace"
            }
        },
        "size": NUM_DOCS_TO_SHOW 
    }
    
    resp = es.search(index=INDEX_DOCS, body=search_body)
    hits = resp['hits']['hits']
    
    if not hits:
        print(f"\nNessun documento trovato per source='{source_to_check}'.")
        return

    # Ciclo risultati
    for i, hit in enumerate(hits, 1):
        doc = hit['_source']
        es_id = hit['_id']
        doc_id = doc.get('document_id')

        # Contiamo figure e tabelle collegate
        n_figures = 0
        n_tables = 0
        if doc_id:
            if es.indices.exists(index=INDEX_FIGURES):
                q_fig = {"query": {"term": {"paper_id": doc_id}}}
                n_figures = es.count(index=INDEX_FIGURES, body=q_fig)['count']
            
            if es.indices.exists(index=INDEX_TABLES):
                q_tab = {"query": {"term": {"paper_id": doc_id}}}
                n_tables = es.count(index=INDEX_TABLES, body=q_tab)['count']

        # Stampa informazioni documento
        print(f"\n\nDOCUMENTO {i}/{len(hits)} ({source_to_check})")
        print(f"Titolo:        {doc.get('title')}")
        print(f"ID Documento:  {doc_id}")
        print(f"ID Elastic:    {es_id}")
        print(f"Data:          {doc.get('date')}")
        print(f"Autori:        {doc.get('authors')}")
        print(f"URL:           {doc.get('pdf_url')}")
        print(f"File Locale:   {doc.get('local_file_saved')}")

        print(f"\nCONTENUTI COLLEGATI:")
        print(f"   Figure:   {n_figures}")
        print(f"   Tabelle:  {n_tables}")

        abstract = doc.get('abstract') or ""
        print(f"\nABSTRACT (Primi 100 caratteri):\n{abstract[:100]}...")

        full_text = doc.get('full_text') or ""
        # Pulizia per visualizzazione compatta (rimuove newline multipli)
        clean_text = " ".join(full_text[:200].split())
        print(f"\nFULL TEXT (Primi 200 caratteri):\n{clean_text}...")

if __name__ == "__main__":
    verify_content()