import os
from elasticsearch import helpers
from figures_extractor import parse_html_figures
from config import INDEX_FIGURES_NAME, OUTPUT_DIR, inizialize_es

def index_figures(es):
    
    # Setup Indice Figure
    setup_figure_index(es)

    # Lettura File e Elaborazione
    if not os.path.exists(OUTPUT_DIR):
        print(f"Cartella {OUTPUT_DIR} mancante.")
        return

    files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".html")]
    print(f"Trovati {len(files)} file. Inizio estrazione figure...")

    all_actions = []

    for filename in files:
        paper_id = filename.replace(".html", "")
        file_path = os.path.join(OUTPUT_DIR, filename)
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            
            # Estrazione Figure per ogni file
            figures = parse_html_figures(html_content, paper_id)
            
            if figures:
                print(f"   {paper_id[:30]}... -> Trovate {len(figures)} figure")
                for fig in figures:
                    action = {
                        "_index": INDEX_FIGURES_NAME,
                        "_id": f"{fig['paper_id']}_{fig['figure_id']}",
                        "_source": fig
                    }
                    all_actions.append(action)
            else:
                print(f"   {paper_id[:30]}... -> Nessuna figura")


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
                "paper_id": {"type": "keyword"},
                "figure_id": {"type": "keyword"}, # Es. "S1.F1"
                
                "img_url": {"type": "keyword"},   # URL dell'immagine (non analizzato)
                
                # Usiamo l'analyzer built-in "english"
                "caption": {"type": "text", "analyzer": "english"}, 
                "mentions": {"type": "text", "analyzer": "english"},
                "context_paragraphs": {"type": "text", "analyzer": "english"}
            }
        }
    }

    es_client.indices.create(index=INDEX_FIGURES_NAME, body=index_body)
    print(f"Indice figure '{INDEX_FIGURES_NAME}' creato")

if __name__ == "__main__":
    es_client = inizialize_es()
    index_figures(es_client)