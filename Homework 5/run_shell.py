import sys
from elasticsearch import ConnectionError
from src.config import Config
from src.core import get_es_client

# --- CONFIGURAZIONE CAMPI DI RICERCA (Boosting) ---
# Definiamo dove cercare e quanto pesare i campi.

# Documenti: Titolo molto importante (^3), Abstract importante (^2)
CONTENT_FIELDS = ["title^3", "abstract^2", "full_text", "authors", "document_id"]

# Tabelle: Caption fondamentale, Contenuto tabella, Contesto
TABLE_FIELDS = ["caption^3", "body_content^2", "mentions", "context_paragraphs", "table_id", "paper_id"]

# Figure: Caption fondamentale, Contesto
FIGURE_FIELDS = ["caption^3", "mentions", "context_paragraphs", "figure_id", "paper_id"]

def choose_index():
    """
    Menu interattivo per scegliere l'indice.
    Restituisce: (tipo_logico, [lista_indici_reali])
    """
    print("\n--- SELEZIONE MODALITÀ ---")
    print(" 1) Documenti (Full Text)")
    print(" 2) Tabelle (Caption + Contenuto + Contesto)")
    print(" 3) Figure (Caption + Contesto)")
    print(" 4) Globale (Cerca in tutti gli indici)")
    
    choice = input("Scelta [1-4, q per uscire]: ").strip()

    if choice.lower() == "q":
        return None, None

    # Mappatura usando le costanti della Config centralizzata
    if choice == "1":
        return "docs", [Config.INDEX_DOCS]
    if choice == "2":
        return "tables", [Config.INDEX_TABLES]
    if choice == "3":
        return "figures", [Config.INDEX_FIGURES]
    if choice == "4":
        return "all", [Config.INDEX_DOCS, Config.INDEX_TABLES, Config.INDEX_FIGURES]

    print("Scelta non valida.")
    return choose_index()

def build_query(index_type, query_string):
    """Costruisce la query Elasticsearch con highlighting."""
    
    if index_type == "docs":
        fields = CONTENT_FIELDS
    elif index_type == "tables":
        fields = TABLE_FIELDS
    elif index_type == "figures":
        fields = FIGURE_FIELDS
    else:
        fields = CONTENT_FIELDS

    return {
        "query": {
            "query_string": {
                "query": query_string,
                "fields": fields,
                "default_operator": "AND"
            }
        },
        "highlight": {
            "fields": { "*": {} },
            # Colore Giallo ANSI per il terminale
            "pre_tags": ["\033[93m"], 
            "post_tags": ["\033[0m"]  
        },
        "size": 5 # Limitiamo a 5 risultati per leggibilità nel terminale
    }

def print_hit(hit, logic_type):
    """Formatta e stampa il risultato in base al tipo."""
    src = hit["_source"]
    score = hit.get("_score", 0)
    origin = src.get('source', 'UNKNOWN').upper()
    highlights = hit.get("highlight", {})

    # Helper per prendere testo evidenziato o originale troncato
    def get_val(field, max_len=300):
        if field in highlights:
            return "... " + " ... ".join(highlights[field]) + " ..."
        
        val = src.get(field, "")
        if isinstance(val, list):
            val = " ".join(val)
        val = str(val).replace("\n", " ")
        
        if len(val) > max_len:
            return val[:max_len] + "..."
        return val

    print(f"\n" + "="*60)
    print(f" [{origin}] Score: {score:.3f} | Indice: {hit['_index']}")
    print("-" * 60)

    # Visualizzazione specifica per tipo
    if logic_type == "docs":
        print(f"ID:      {src.get('document_id')}")
        print(f"Titolo:  {get_val('title', 150)}")
        print(f"Autori:  {get_val('authors', 100)}")
        print(f"Data:    {src.get('date')}")
        print(f"Link:    {src.get('pdf_url')}")
        print(f"\nAbstract/Snippet:\n{get_val('abstract', 300)}")
        if 'full_text' in highlights:
            print(f"\nMatch nel testo:\n{get_val('full_text')}")

    elif logic_type == "tables":
        print(f"Paper ID: {src.get('paper_id')} | Table ID: {src.get('table_id')}")
        print(f"\nCaption:\n{get_val('caption', 300)}")
        print(f"Contenuto:\n{get_val('body_content', 200)}")
        if 'context_paragraphs' in highlights:
             print(f"\nContesto:\n{get_val('context_paragraphs')}")

    elif logic_type == "figures":
        print(f"Paper ID: {src.get('paper_id')} | Fig ID: {src.get('figure_id')}")
        print(f"URL Img:  {src.get('img_url')}")
        print(f"\nCaption:\n{get_val('caption', 300)}")
        if 'context_paragraphs' in highlights:
             print(f"\nContesto:\n{get_val('context_paragraphs')}")

def run_shell():
    """Main loop della shell."""
    
    # 1. Connessione (Gestita con fail-fast nel main block)
    es = get_es_client()

    print("\n##################################################")
    print("#   SCIENTIFIC CORPUS SHELL (ArXiv & PubMed)     #")
    print("##################################################")
    print("Tip: usa operatori come AND, OR. Es: \"AI\" AND (nutrition OR food)")
    
    while True:
        # 2. Scelta Indice
        logic_type, target_indices = choose_index()
        if not target_indices:
            print("Arrivederci.")
            break

        # 3. Input Query
        query_string = input("\nQUERY > ").strip()
        if not query_string or query_string.lower() == "q":
            continue

        # 4. Esecuzione su tutti gli indici selezionati
        for idx in target_indices:
            
            # Determina il tipo logico corrente (per formattare l'output)
            current_logic = "docs"
            if idx == Config.INDEX_TABLES: current_logic = "tables"
            if idx == Config.INDEX_FIGURES: current_logic = "figures"

            body = build_query(current_logic, query_string)

            try:
                resp = es.search(index=idx, body=body)
                hits = resp['hits']['hits']
                total = resp['hits']['total']['value']

                if hits:
                    print(f"\n>>> Trovati {total} risultati in '{idx}' (Top 5):")
                    for h in hits:
                        print_hit(h, current_logic)
                
            except Exception as e:
                # Gestiamo l'errore per singolo indice senza bloccare la shell
                print(f"Errore ricerca su {idx}: {e}")

if __name__ == "__main__":
    try:
        run_shell()
    except ConnectionError as e:
        print(f"\n[ERRORE CRITICO] {e}")
        print("Verifica che Elasticsearch sia avviato.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nUscita forzata.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERRORE INATTESO] {e}")
        sys.exit(1)