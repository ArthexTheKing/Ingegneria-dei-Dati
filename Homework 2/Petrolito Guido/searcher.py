from elasticsearch import Elasticsearch
import subprocess

# Avvio automatico di indexer.py
print("Avvio di indexer.py per creare/aggiornare gli indici...")
subprocess.run(["python3", "indexer.py"])

# Nome dell'indice e connessione
INDEX_NAME = "files"
ES_URL = "http://localhost:9200"
es = Elasticsearch(ES_URL)

def cerca(query_str):
    query_str = query_str.strip()
    if not query_str:
        print("Inserisci una query valida.\n")
        return

    # === QUERY PER IL NOME ===
    if query_str.startswith("nome "):
        terms = query_str[5:].strip().replace('"', '')

        # Se l'utente scrive il nome completo (es: cardiologia.txt)
        if terms.endswith(".txt"):
            query = {
                "term": {"nome.raw": terms}
            }
        else:
            # Se scrive solo una parte (es: cardiologia)
            query = {
                "wildcard": {"nome.raw": f"*{terms}*"}
            }

    # === QUERY PER IL CONTENUTO ===
    elif query_str.startswith("contenuto "):
        terms = query_str[10:].strip().replace('"', '')
        if '"' in query_str:
            query = {"match_phrase": {"contenuto": terms}}
        else:
            query = {"match": {"contenuto": terms}}

    else:
        print("Sintassi non valida. Usa 'nome <termine>' o 'contenuto <termine>'.\n")
        return

    # === ESECUZIONE QUERY ===
    try:
        res = es.search(index=INDEX_NAME, query=query)
    except Exception as e:
        print(f"Errore durante la ricerca: {e}\n")
        return

    hits = res.get('hits', {}).get('hits', [])

    if not hits:
        print("Nessun documento trovato.\n")
    else:
        print(f"Trovati {len(hits)} documenti:\n")
        for h in hits:
            nome = h["_source"].get("nome", "—")
            score = h.get("_score", 0)
            print(f"{nome} (score: {score:.2f})")
        print("")

if __name__ == "__main__":
    print("Connessione a Elasticsearch stabilita.\n")
    print("Sistema di ricerca – digita una query (es: contenuto 'sistema nervoso')")
    print("Scrivi 'exit' per terminare.\n")

    while True:
        query = input("> ")
        if query.lower() == "exit":
            break
        cerca(query)
