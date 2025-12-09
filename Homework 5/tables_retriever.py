import os
from elasticsearch import helpers
from tables_extractor import parse_html_tables
from config import INDEX_TABLES_NAME, OUTPUT_DIR_ARXIV, inizialize_es

def index_tables(es):
    
    # Setup Indice Tabelle
    setup_table_index(es)

    # Lettura File e Elaborazione
    if not os.path.exists(OUTPUT_DIR_ARXIV):
        print(f"Cartella {OUTPUT_DIR_ARXIV} non trovata")
        return

    files = [f for f in os.listdir(OUTPUT_DIR_ARXIV) if f.endswith(".html")]
    print(f"Trovati {len(files)} file HTML in '{OUTPUT_DIR_ARXIV}'. Inizio estrazione tabelle...")
    all_table_actions = []
    total_tables_found = 0

    for filename in files:
        file_path = os.path.join(OUTPUT_DIR_ARXIV, filename)
        
        # ID dell'articolo (dal nome file o da logica custom)
        paper_id = filename.replace(".html", "")
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            
            # Estrazione Tabelle per ogni file
            tables = parse_html_tables(html_content, paper_id)
            
            if tables:
                print(f"   {paper_id[:30]}... -> Trovate {len(tables)} tabelle")
                total_tables_found += len(tables)
                
                # Preparazione per Bulk Indexing
                for t in tables:
                    action = {
                        "_index": INDEX_TABLES_NAME,
                        "_id": f"{t['paper_id']}_{t['table_id']}", # ID univoco: PaperID + TableID
                        "_source": t
                    }
                    all_table_actions.append(action)
            else:
                print(f"   {paper_id[:30]}... -> Nessuna tabella")

        except Exception as e:
            print(f"   Errore lettura {filename}: {e}")

    # Indicizzazione Bulk
    if all_table_actions:
        print(f"Indicizzazione bulk di {len(all_table_actions)} tabelle...")
        try:
            success, errors = helpers.bulk(es, all_table_actions)
            es.indices.refresh(index=INDEX_TABLES_NAME)
            print(f"Completato: {success} tabelle indicizzate\n")
            if errors:
                print(f"Errori: {errors}\n\n")
        except Exception as e:
            print(f"Errore critico bulk: {e}\n\n")
    else:
        print("Nessuna tabella trovata")


def setup_table_index(es_client):
    if es_client.indices.exists(index=INDEX_TABLES_NAME):
        print(f"L'indice tabelle '{INDEX_TABLES_NAME}' esiste. Reset in corso...")
        es_client.indices.delete(index=INDEX_TABLES_NAME)
    
    index_body = {
        "mappings": {
            "properties": {
                "paper_id": {"type": "keyword"},            # ID arXiv reale (es. 2511.11104)
                "paper_title_slug": {"type": "keyword"},    # Nome file (es. Text_To_Speech)
                "table_id": {"type": "keyword"},            # ID Tabella (es. S1.T1)
                
                "caption": {
                    "type": "text", 
                    "analyzer": "english"
                },

                "body_content": {
                    "type": "text", 
                    "analyzer": "english"
                },
                
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

    es_client.indices.create(index=INDEX_TABLES_NAME, body=index_body)
    print(f"Indice tabelle '{INDEX_TABLES_NAME}' creato")

if __name__ == "__main__":
    es_client = inizialize_es()
    index_tables(es_client)