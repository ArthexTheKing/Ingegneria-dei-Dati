import os
import string
from elasticsearch import Elasticsearch
from avvioContainer import avvia_container  # import dal nuovo file
import time


DATA_DIR = "data"

# === ANALYZER ===
def analyzer(text):
    # Trasforma il testo in minuscolo e Rimuove tutta la punteggiatura.
    text = text.lower().translate(str.maketrans("", "", string.punctuation))
    # Rimuove gli spazi bianchi ''
    return text.split()

# === CONNESSIONE ===
def connetti_es():
    try:
        es = Elasticsearch("http://localhost:9200")
        if not es.ping():
            raise Exception
        # print("Elasticsearch connesso.")
        return es
    except:
        # print("Elasticsearch non è raggiungibile: controlla Docker.")
        exit(1)

# === CREAZIONE INDICE ===
def crea_indice(es):
    if es.indices.exists(index="files"):
        es.indices.delete(index="files")

    mapping = {
        "settings": {
            "analysis": {
                "analyzer": {
                    "italian_analyzer": {
                        "type": "standard",
                        "stopwords": "_italian_"
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "nome": {
                    "type": "text",
                    "fields": {
                        "raw": {"type": "keyword"}
                    },
                    "analyzer": "italian_analyzer"
                },
                "contenuto": {
                    "type": "text",
                    "analyzer": "italian_analyzer"
                }
            }
        }
    }

    es.indices.create(index="files", body=mapping)
    # print("Indice 'files' creato con doppio campo nome (text + keyword).")


import os
import time

def indicizza_documenti(es):
    start = time.time()
    count = 0

    for filename in os.listdir(DATA_DIR):
        path = os.path.join(DATA_DIR, filename)
        if filename.endswith(".txt"):
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                contenuto = f.read()
            # Usiamo il nome del file come ID per aggiornare documenti esistenti
            es.index(
                index="files",
                id=filename,
                document={"nome": filename, "contenuto": contenuto}
            )
            count += 1

    end = time.time()
    print(f"Indicizzati {count} file in {end - start:.2f} secondi.")



# === MAIN ===
if __name__ == "__main__":
    avvia_container()  # viene chiamato dal modulo esterno
    es = connetti_es()
    crea_indice(es)
    indicizza_documenti(es)