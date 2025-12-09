import os
from elasticsearch import helpers
from figures_extractor import parse_html_figures
from config import INDEX_FIGURES_NAME, OUTPUT_DIR_ARXIV, inizialize_es

def index_figures(es):
    
    # Setup Indice Figure
    setup_figure_index(es)

    # Lettura File e Elaborazione
    if not os.path.exists(OUTPUT_DIR_ARXIV):
        print(f"Cartella {OUTPUT_DIR_ARXIV} mancante.")
        return

    files = [f for f in os.listdir(OUTPUT_DIR_ARXIV) if f.endswith(".html")]
    print(f"Trovati {len(files)} file. Inizio estrazione figure...")

    all_actions = []

    for filename in files:
        filename_stem = filename.replace(".html", "")
        file_path = os.path.join(OUTPUT_DIR_ARXIV, filename)
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            
            # Estrazione Figure per ogni file
            figures = parse_html_figures(html_content, filename_stem)
            
            if figures:
                print(f"   {filename_stem[:30]}... -> Trovate {len(figures)} figure")
                for fig in figures:
                    action = {
                        "_index": INDEX_FIGURES_NAME,
                        "_id": f"{fig['paper_id']}_{fig['figure_id']}",
                        "_source": fig
                    }
                    all_actions.append(action)
            else:
                print(f"   {filename_stem[:30]}... -> Nessuna figura")


        except Exception as e:
            print(f"   Errore {filename}: {e}")

    if all_actions:
        print(f"Indicizzazione bulk di {len(all_actions)} figure...")
        try:
            success, errors = helpers.bulk(es, all_actions)
            es.indices.refresh(index=INDEX_FIGURES_NAME)
            print(f"Completato: {success} figure indicizzate")
            if errors: 
                print(f"Errori: {errors}")
        except Exception as e:
                    print(f"Errore critico bulk: {e}\n\n")
    else:
        print("Nessuna figura trovata")


def setup_figure_index(es_client):
    if es_client.indices.exists(index=INDEX_FIGURES_NAME):
        print(f"L'indice figure '{INDEX_FIGURES_NAME}' esiste. Reset in corso...")
        es_client.indices.delete(index=INDEX_FIGURES_NAME)
    
    index_body = {
        "mappings": {
            "properties": {
                # Identificativi
                "paper_id": {"type": "keyword"},          # ID arXiv reale (es. 2511.11104)
                "paper_title_slug": {"type": "keyword"},  # Nome file (es. Text_To_Speech)
                "figure_id": {"type": "keyword"},         # ID Figura (es. S1.F1)
                
                # Dati Immagine
                "img_url": {"type": "keyword"},           # URL Web assoluto
                "local_src": {"type": "keyword"},         # Path relativo originale
                
                # Contenuto Testuale (Analyzer English)
                "caption": {
                    "type": "text", 
                    "analyzer": "english"
                },
                
                # Contesto e Citazioni
                "mentions": {
                    "type": "text", 
                    "analyzer": "english"
                },
                "context_paragraphs": {
                    "type": "text", 
                    "analyzer": "english"
                }
            }
        }
    }

    es_client.indices.create(index=INDEX_FIGURES_NAME, body=index_body)
    print(f"Indice figure '{INDEX_FIGURES_NAME}' creato")

if __name__ == "__main__":
    es_client = inizialize_es()
    index_figures(es_client)