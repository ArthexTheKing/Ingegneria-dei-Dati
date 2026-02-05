# per eseguire: python -m test.verify_figures

from src.core.es import get_es_client
from src.config import Config

def verify_figures():
    es = get_es_client()
    
    # Indici
    INDEX_DOCS = Config.INDEX_DOCS
    INDEX_FIGURES = Config.INDEX_FIGURES

    # Configurazione Test
    source_to_check = 'pubmed'  # Cambia in 'pubmed' se necessario
    NUM_TO_SHOW = 5            # Quante figure mostrare

    # Statistiche generali
    print("\nStatistiche Indice Figure")

    
    # Controllo esistenza
    if not es.indices.exists(index=INDEX_FIGURES):
        print(f"L'indice '{INDEX_FIGURES}' non esiste.")
        return

    # Conteggi totali
    count = es.count(index=INDEX_FIGURES)['count']
    print(f"Totale figure in '{INDEX_FIGURES}': {count}")

    query_arxiv = {"query": {"term": {"source": "arxiv"}}}
    count_arxiv = es.count(index=INDEX_FIGURES, body=query_arxiv)['count']
    print(f"Figure da ArXiv:  {count_arxiv}")

    query_pubmed = {"query": {"term": {"source": "pubmed"}}}
    count_pubmed = es.count(index=INDEX_FIGURES, body=query_pubmed)['count']
    print(f"Figure da PubMed: {count_pubmed}")

    # Recupero figure
    print(f"Recupero {NUM_TO_SHOW} figure CASUALI con source='{source_to_check}'...")

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
    
    resp = es.search(index=INDEX_FIGURES, body=search_body)
    hits = resp['hits']['hits']
    
    if not hits:
        print(f"Nessuna figura trovata per source='{source_to_check}'.")
        return

    # Ciclo risultati
    for i, hit in enumerate(hits, 1):
        fig = hit['_source']
        es_id = hit['_id']
        
        figure_id = fig.get('figure_id')
        paper_id = fig.get('paper_id')
        
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

        # Stampa informazioni figura
        print(f"\n\nFIGURA {i}/{len(hits)} ({source_to_check})")

        print(f"ID Figura:     {figure_id}")
        print(f"ID Elastic:    {es_id}")
        print(f"Paper ID:      {paper_id}")
        print(f"Menzioni:      {len(fig.get('mentions', []))} nel testo")
        img_url = fig.get('img_url') or "N/A"
        print(f"URL Immagine:  {img_url}")
        
        if parent_found:
            print(f"\nDOCUMENTO PADRE TROVATO:")
            print(f"   Titolo: {parent_title[:80]}...")
        else:
            print(f"\nATTENZIONE: Documento padre '{paper_id}' NON trovato in '{INDEX_DOCS}'!")
            print(f"   (Verifica che l'ID corrisponda esattamente)")

        caption = fig.get('caption') or ""
        clean_cap = " ".join(caption.split())
        print(f"\nCAPTION (Primi 200 caratteri):\n{clean_cap[:200]}...")

        context = fig.get('context_paragraphs', [])
        if context:
            clean_ctx = " ".join(context[0].split())
            print(f"\nCONTESTO TROVATO (Snippet):\n{clean_ctx[:150]}...")

if __name__ == "__main__":
    verify_figures()