from config import INDEX_NAME

def execute_search(es_client, query_string):
    parts = query_string.strip().split(':', 1)
    
    if len(parts) == 2:
        field, terms = parts[0].strip().lower(), parts[1].strip()
    else:
        field = "contenuto"
        terms = query_string.strip()

    query_body = None
    search_field = None
    
    if field == "nome":
        search_field = "nome_file"
        terms_clean = terms.strip('"').lower() 
        
        # Wildcard Search sul campo keyword
        query_body = {
            "query": {
                "wildcard": {
                    search_field: {
                        "value": f"*{terms_clean}*"
                    }
                }
            }
        }
    
    elif field == "contenuto":
        search_field = "contenuto_file"
        
        if terms.startswith('"') and terms.endswith('"'):
            # Phrase Query
            phrase = terms.strip('"')
            query_body = {"query": {"match_phrase": {search_field: phrase}}}
        else:
            # Match Query (Ricerca per termini)
            if terms.lower() == "retropropagazione":
                # Correzione logica per backpropagation
                terms_expanded = "retropropagazione OR backpropagation"
                query_body = {"query": {"query_string": {"query": terms_expanded, "default_field": search_field}}}
            else:
                query_body = {"query": {"match": {search_field: terms}}}
    else:
        print(f"Errore: parola chiave '{field}' non riconosciuta.")
        return

    try:
        res = es_client.search(index=INDEX_NAME, body=query_body)
    except Exception:
        return

    # Stampa dei risultati
    print("\n" + "="*50)
    print(f"Query: {query_string}")
    total_hits = res['hits']['total']['value']
    print(f"Risultati: {total_hits}")
    
    if total_hits > 0:
        for hit in res['hits']['hits']:
            file_name = hit['_source']['nome_file']
            score = hit['_score']
            print(f"[{score:.3f}] - {file_name}")
    print("="*50 + "\n")

def main_searcher(es_client):
    if not es_client: return
    
    print("\n--- Sistema di Ricerca Avviato ---")
    print(" SINTASSI: nome:<parola> o contenuto:<parola/\"phrase query\">")
    print(" Digita 'esci' per terminare.")
    
    while True:
        query_string = input("QUERY > ")
        if query_string.lower() == 'esci': break
        if query_string.strip():
            execute_search(es_client, query_string)