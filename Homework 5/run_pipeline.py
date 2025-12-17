import os, sys
from elasticsearch import helpers, Elasticsearch
from src.config import Config
from src.core import get_es_client
from src.ingestion import download_arxiv_data, download_pubmed_data
from src.processing import extract_multimedia

def setup_indices(es: Elasticsearch):
    """Crea o resetta gli indici in Elasticsearch."""
    # Mappings semplificati per brevità
    mappings_text = {"properties": {"title": {"type": "text", "analyzer": "english"}, "full_text": {"type": "text", "analyzer": "english"}}}
    mappings_media = {"properties": {"caption": {"type": "text", "analyzer": "english"}, "context_paragraphs": {"type": "text", "analyzer": "english"}}}

    indices = [
        (Config.INDEX_DOCS, mappings_text),
        (Config.INDEX_TABLES, mappings_media),
        (Config.INDEX_FIGURES, mappings_media)
    ]

    for idx_name, mapping in indices:
        if es.indices.exists(index=idx_name):
            es.indices.delete(index=idx_name)
        es.indices.create(index=idx_name, body={"mappings": mapping})
        print(f"Indice creato: {idx_name}")

def run():
    es = get_es_client()

    # 1. Setup
    setup_indices(es)

    # 2. Download e Indicizzazione Documenti (Docs)
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
    
    # 3. Estrazione e Indicizzazione Figure/Tabelle
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

    print("\nPipeline completata.")

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