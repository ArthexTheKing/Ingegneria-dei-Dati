# motore_docker_elastic.py
import os
import time
import shlex
from elasticsearch import Elasticsearch, helpers
from elasticsearch.exceptions import NotFoundError

# ===============================
# CONFIGURAZIONE
# ===============================
DATA_DIR = "dati"
INDEX = "file_txt"

# Connessione Elasticsearch: forziamo la compatibilità con l'API 8.x
# Questo è necessario perché il server è 8.9.0
es = Elasticsearch(
    "http://localhost:9200", 
    verify_certs=False,
    # L'intestazione corretta per la v8 è compatibile con 8
    headers={"accept": "application/vnd.elasticsearch+json; compatible-with=8"} 
)
# ===============================
# FUNZIONI
# ===============================

def crea_file_di_test():
    os.makedirs(DATA_DIR, exist_ok=True)
    files_content = {
        "ricetta_pasta.txt": """Titolo: Pasta al pomodoro
Ingredienti: pasta, pomodori, basilico, olio, sale
Preparazione: cuocere la pasta in acqua salata, preparare la salsa con i pomodori e condire.
Tempo di cottura: 10 minuti""",
        "lezione_ai.txt": """Appunti della lezione su intelligenza artificiale.
L'intelligenza artificiale studia algoritmi capaci di apprendere dai dati.
Si è parlato di machine learning supervisionato e reti neurali.""",
        "appunti_database.txt": """Argomento: Database e linguaggio SQL
Un database è un insieme organizzato di dati. Abbiamo visto le operazioni SELECT, JOIN e GROUP BY.
Esempi pratici in PostgreSQL.""",
        "esperimento_bio.txt": """Descrizione esperimento biologico sui batteri.
I dati raccolti mostrano una crescita costante.
Analisi statistica con Python e librerie scientifiche.""",
        "progetto_python.txt": """Progetto di programmazione in Python.
Obiettivo: analizzare dataset e creare grafici.
Librerie utilizzate: Pandas, Matplotlib e Scikit-learn.""",
        "guida_viaggio.txt": """Guida di viaggio a Roma.
Consigli su musei, ristoranti e monumenti principali.
Periodo migliore: primavera o autunno.""",
        "articolo_ml.txt": """Articolo su Machine Learning applicato al riconoscimento immagini.
Reti neurali convoluzionali e deep learning sono stati i temi principali.
Si è discusso anche di overfitting e validazione incrociata.""",
        "diario_universita.txt": """Oggi ho seguito il corso di analisi dei dati.
Il professore ha spiegato come funziona la regressione lineare.
Molto interessante la parte pratica con notebook Python.""",
        "schema_sql.txt": """CREATE TABLE studenti (
    id INT PRIMARY KEY,
    nome VARCHAR(50),
    corso VARCHAR(50)
);
Esempio di query: SELECT nome FROM studenti WHERE corso = 'Informatica';""",
        "note_personali.txt": """Appunti personali su diversi argomenti.
Promemoria per esame di database e progetto di intelligenza artificiale.
Ricordarsi di aggiornare la repository su GitHub."""
    }

    for fname, content in files_content.items():
        with open(os.path.join(DATA_DIR, fname), "w", encoding="utf-8") as f:
            f.write(content)
    print(f"✅ Creati {len(files_content)} file in /{DATA_DIR}")

# =================================
# CREAZIONE INDICE
# =================================

def crea_indice():
    mapping = {
        "settings": {
            "analysis": {
                # Definiamo i componenti
                "tokenizer": {
                    "filename_tokenizer": {
                        "type": "pattern",
                        "pattern": "[^A-Za-z0-9]+" # Splitta in base a caratteri non alfanumerici
                    }
                },
                # Definiamo l'analyzer personalizzato (deve essere "custom")
                "analyzer": {
                    "filename_analyzer": {
                        "type": "custom", # <-- AGGIUNTO QUESTO!
                        "tokenizer": "filename_tokenizer",
                        "filter": ["lowercase"] 
                    }
                    # NOTA: Non si definisce l'analyzer standard "italian" qui.
                }
            }
        },
        "mappings": {
            "properties": {
                "nome": {
                    "type": "text",
                    "analyzer": "filename_analyzer", # Usiamo l'analyzer PERSONALIZZATO
                    "fields": {"raw": {"type": "keyword"}}
                },
                "contenuto": {
                    "type": "text",
                    "analyzer": "italian" # Usiamo l'analyzer di sistema "italian"
                },
                "path": {"type": "keyword", "index": False}
            }
        }
    }

    # Blocco per gestire la creazione/verifica dell'indice
    try:
        # Se l'indice esiste, lo stampiamo e usciamo, altrimenti si crea
        if es.indices.exists(index=INDEX):
            print(f"ℹ️ Indice '{INDEX}' già esistente.")
        else:
            # Crea l'indice con il mapping corretto
            es.indices.create(index=INDEX, body=mapping)
            print(f"✅ Indice '{INDEX}' creato con successo!")
    except Exception as e:
        print(f"❌ Errore durante la creazione o verifica dell'indice: {e}")
        print("💡 Suggerimento: Verifica che il server Elasticsearch sia in esecuzione su http://localhost:9200 e prova a riavviarlo.")
# =================================
# INDICIZZAZIONE FILE
# =================================

def iter_docs():
    for fname in os.listdir(DATA_DIR):
        if not fname.endswith(".txt"):
            continue
        path = os.path.join(DATA_DIR, fname)
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        nome_no_ext = os.path.splitext(fname)[0]
        yield {
            "_index": INDEX,
            "_id": fname,
            "_source": {
                "nome": nome_no_ext,
                "contenuto": text,
                "path": path
            }
        }

def indicizza_file():
    start = time.time()
    helpers.bulk(es, iter_docs())
    elapsed = time.time() - start
    print(f"✅ Indicizzazione completata in {elapsed:.3f} s")

# =================================
# RICERCA INTERATTIVA
# =================================

def build_query(campo, valore):
    if " " in valore.strip():
        return {"match_phrase": {campo: valore}}
    else:
        return {"match": {campo: valore}}

def ricerca_interattiva():
    print("\n🔎 Inserisci query (es: nome:ricetta oppure contenuto:\"intelligenza artificiale\"). 'exit' per uscire.")
    while True:
        s = input("> ").strip()
        if s.lower() in ("exit","quit"):
            break
        if ":" not in s:
            print("❌ Errore: usa sintassi campo:termini")
            continue
        campo, resto = s.split(":", 1)
        campo = campo.strip()
        resto = resto.strip()
        try:
            parts = shlex.split(resto)
            valore = " ".join(parts)
        except ValueError:
            valore = resto.strip('"')
        body = {"query": build_query(campo, valore)}
        res = es.search(index=INDEX, query=body["query"], size=50)
        hits = res["hits"]["hits"]
        print(f"Trovati {len(hits)} risultati (took {res['took']}ms):")
        for h in hits:
            src = h["_source"]
            snippet = src.get("contenuto","")[:200] + "..."
            print(f" - {h['_id']}  (nome: {src.get('nome')})\n   snippet: {snippet}")
        print()

# =================================
# MENU
# =================================

def main():
    while True:
        print("\n=== MOTORE DI RICERCA TXT SU ELASTICSEARCH ===\n")
        print("1. Crea file di test nella cartella /dati")
        print("2. Crea indice Elasticsearch")
        print("3. Indicizza file")
        print("4. Avvia ricerca interattiva")
        print("5. Esegui tutto automaticamente (1→4)")
        print("0. Esci\n")

        scelta = input("Seleziona un'opzione: ").strip()
        if scelta == "1":
            crea_file_di_test()
        elif scelta == "2":
            crea_indice()
        elif scelta == "3":
            indicizza_file()
        elif scelta == "4":
            ricerca_interattiva()
        elif scelta == "5":
            crea_file_di_test()
            crea_indice()
            indicizza_file()
            ricerca_interattiva()
        elif scelta == "0":
            print("👋 Uscita.")
            break
        else:
            print("❌ Scelta non valida")

# =================================
# AVVIO
# =================================
if __name__ == "__main__":
    main()
