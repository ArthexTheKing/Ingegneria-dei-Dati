# per eseguire: python -m test.verify_tables

from src.core.es import get_es_client
from src.config import Config

def verify_tables():
    es = get_es_client()
    
    # Indici
    INDEX_DOCS = Config.INDEX_DOCS
    INDEX_TABLES = Config.INDEX_TABLES

    # Configurazione Test
    source_to_check = 'pubmed'  # Cambia in 'pubmed' se necessario
    NUM_TO_SHOW = 5            # Quante tabelle mostrare

    # Statistiche generali
    print("\nStatistiche Indice Tabelle")
    
    # Controllo esistenza
    if not es.indices.exists(index=INDEX_TABLES):
        print(f"L'indice '{INDEX_TABLES}' non esiste.")
        return

    # Conteggi totali
    count = es.count(index=INDEX_TABLES)['count']
    print(f"Totale tabelle in '{INDEX_TABLES}': {count}")

    query_arxiv = {"query": {"term": {"source": "arxiv"}}}
    count_arxiv = es.count(index=INDEX_TABLES, body=query_arxiv)['count']
    print(f"Tabelle da ArXiv:  {count_arxiv}")

    query_pubmed = {"query": {"term": {"source": "pubmed"}}}
    count_pubmed = es.count(index=INDEX_TABLES, body=query_pubmed)['count']
    print(f"Tabelle da PubMed: {count_pubmed}")
    
    # Recupero tabelle
    print(f"Recupero {NUM_TO_SHOW} tabelle CASUALI con source='{source_to_check}'...")

    search_body = {
        "query": {
            "function_score": {
                "query": {"term": {"source": source_to_check}}, 
                "random_score": {}, 
                "boost_mode": "replace"
            }
        },
        "size": NUM_TO_SHOW 
    }
    
    resp = es.search(index=INDEX_TABLES, body=search_body)
    hits = resp['hits']['hits']
    
    if not hits:
        print(f"Nessuna tabella trovata per source='{source_to_check}'.")
        return

    # Ciclo risultati
    for i, hit in enumerate(hits, 1):
        tbl = hit['_source']
        es_id = hit['_id']
        
        table_id = tbl.get('table_id')
        paper_id = tbl.get('paper_id')
        
        # Verifichiamo se il documento padre esiste nell'indice DOCS
        parent_title = "N/A"
        parent_found = False
        
        if es.indices.exists(index=INDEX_DOCS) and paper_id:
            q_parent = {
                "query": {"term": {"document_id": paper_id}},
                "size": 1
            }
            resp_parent = es.search(index=INDEX_DOCS, body=q_parent)
            
            if resp_parent['hits']['hits']:
                parent_found = True
                parent_title = resp_parent['hits']['hits'][0]['_source'].get('title')

        # Stampa informazioni tabella
        print(f"\n\nTABELLA {i}/{len(hits)} ({source_to_check})")

        print(f"ID Tabella:    {table_id}")
        print(f"ID Elastic:    {es_id}")
        print(f"Paper ID:      {paper_id}")
        print(f"Menzioni:      {len(tbl.get('mentions', []))} nel testo")
        
        if parent_found:
            print(f"\nDOCUMENTO PADRE TROVATO")
            print(f"   Titolo: {parent_title[:80]}...")
        else:
            print(f"\nATTENZIONE: Documento padre '{paper_id}' NON trovato in '{INDEX_DOCS}'!")
            print(f"   (Verifica che l'ID corrisponda esattamente, inclusi spazi o estensioni)")

        caption = tbl.get('caption') or ""
        # Pulizia visuale
        clean_cap = " ".join(caption.split())
        print(f"\nCAPTION (Primi 150 caratteri):\n{clean_cap[:150]}...")

        body = tbl.get('body_content') or ""
        # Pulizia visuale
        clean_body = " ".join(body.split())
        print(f"\nCONTENUTO TABELLA (Primi 200 caratteri):\n{clean_body[:200]}...")

if __name__ == "__main__":
    verify_tables()