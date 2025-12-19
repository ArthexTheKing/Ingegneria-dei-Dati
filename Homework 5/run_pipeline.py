import os, sys
from elasticsearch import helpers, Elasticsearch
from src.config import Config
from src.core import get_es_client
from src.ingestion import download_arxiv_data, download_pubmed_data
from src.processing import extract_multimedia

def setup_indices(es: Elasticsearch):
    """
    Crea o resetta gli indici in Elasticsearch con i mapping corretti
    """
    
    # Mapping documenti (INDEX_DOCS)
    mappings_docs = {
        "properties": {
            "source": {"type": "keyword"},              # 'arxiv' o 'pubmed'
            "document_id": {"type": "keyword"},         # ID univoco del documento
            "pdf_url": {"type": "keyword"},             # URL del PDF
            "local_file_saved": {"type": "boolean"},    # Se il file è salvato localmente
            "date": {"type": "date"},                   # Data di pubblicazione
            
            # Testo analizzato
            "title": {"type": "text", "analyzer": "english"},       # Titolo
            "abstract": {"type": "text", "analyzer": "english"},    # Abstract
            "full_text": {"type": "text", "analyzer": "english"},   # Testo completo
            "authors": {"type": "text", "analyzer": "standard"}     # Autori
        }
    }

    # Mapping multimedia (INDEX_TABLES e INDEX_FIGURES)
    mappings_media = {
        "properties": {
            "source": {"type": "keyword"},      # 'arxiv' o 'pubmed'
            "paper_id": {"type": "keyword"},    # ID del documento
            "figure_id": {"type": "keyword"},   # ID della figura
            "table_id": {"type": "keyword"},    # ID della tabella
            "img_url": {"type": "keyword"},     # URL dell'immagine
            
            # Contenuto semantico (Testo)
            "caption": {"type": "text", "analyzer": "english"},             # Didascalia
            "body_content": {"type": "text", "analyzer": "english"},        # Solo per le tabelle
            "mentions": {"type": "text", "analyzer": "english"},            # Riferimenti nel testo
            "context_paragraphs": {"type": "text", "analyzer": "english"}   # Paragrafi di contesto
        }
    }

    indices = [
        (Config.INDEX_DOCS, mappings_docs),
        (Config.INDEX_TABLES, mappings_media),
        (Config.INDEX_FIGURES, mappings_media)
    ]

    print("\nSetup Indici")
    for idx_name, mapping in indices:
        if es.indices.exists(index=idx_name):
            print(f"Eliminazione indice esistente: {idx_name}")
            es.indices.delete(index=idx_name)
        
        es.indices.create(index=idx_name, body={"mappings": mapping})
        print(f"Indice creato: {idx_name}")

def run():
    es = get_es_client()

    # Setup indici
    setup_indices(es)

    # Download e Indicizzazione Documenti (Docs)
    df_arxiv = download_arxiv_data()
    df_pubmed = download_pubmed_data()
    
    # Unione e Indexing Docs
    all_docs = []
    if not df_arxiv.empty: all_docs.extend(df_arxiv.to_dict(orient='records'))
    if not df_pubmed.empty: all_docs.extend(df_pubmed.to_dict(orient='records'))

    if all_docs:
        print(f"Indicizzazione {len(all_docs)} documenti...")
        actions = [{"_index": Config.INDEX_DOCS, "_id": d['document_id'], "_source": d} for d in all_docs]
        helpers.bulk(es, actions)
    
    # Estrazione e Indicizzazione Figure/Tabelle
    print("\nEstrazione Multimediale in corso...")
    
    all_figures = []
    all_tables = []

    # Processiamo i file locali scaricati
    for folder, source in [(Config.OUTPUT_DIR_ARXIV, "arxiv"), (Config.OUTPUT_DIR_PUBMED, "pubmed")]:
        if not os.path.exists(folder): continue
        
        files = [f for f in os.listdir(folder) if f.endswith(".html")]
        for f in files:
            path = os.path.join(folder, f)
            paper_id = f.replace(".html", "")
            
            with open(path, "r", encoding="utf-8") as file_in:
                html = file_in.read()
            
            # Unica chiamata all'extractor
            figs, tabs = extract_multimedia(html, paper_id, source)
            all_figures.extend(figs)
            all_tables.extend(tabs)

    # Bulk Indexing Figure
    if all_figures:
        print(f"Indicizzazione {len(all_figures)} Figure...")
        actions = [{"_index": Config.INDEX_FIGURES, "_id": f"{x['paper_id']}_{x['figure_id']}", "_source": x} for x in all_figures]
        helpers.bulk(es, actions)

    # Bulk Indexing Tabelle
    if all_tables:
        print(f"Indicizzazione {len(all_tables)} Tabelle...")
        actions = [{"_index": Config.INDEX_TABLES, "_id": f"{x['paper_id']}_{x['table_id']}", "_source": x} for x in all_tables]
        helpers.bulk(es, actions)

    print("\nIndicizzazione completata")

if __name__ == "__main__":
    try:
        run()
    except ConnectionError as e:
        print(f"\n[ERRORE CRITICO] {e}")
        print("Assicurati che Docker o il servizio Elasticsearch sia attivo.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERRORE INATTESO] {e}")
        sys.exit(1)