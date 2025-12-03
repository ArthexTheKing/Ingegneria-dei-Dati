from config import inizialize_es, INDEX_TABLES_NAME

def verify_index_tables():
   
    es = inizialize_es()

    # Controllo conteggio totale
    count = es.count(index=INDEX_TABLES_NAME)['count']
    print(f"Totale tabelle nell'indice '{INDEX_TABLES_NAME}': {count}")

    # Recupero di un documento a caso (usiamo una query match_all con size 1)
    resp = es.search(index=INDEX_TABLES_NAME, body={"query": {"match_all": {}}, "size": 1})

    if not resp['hits']['hits']:
        print("Indice vuoto.")
        return

    hit = resp['hits']['hits'][0]
    doc = hit['_source']
    doc_id = hit['_id']

    # Stampa Formattata dei Dati
    print(f"\nDettaglio tabella (ID Documento ES: {doc_id})")

    # Identificativi
    print(f"Paper ID:  {doc.get('paper_id')}")
    print(f"Table ID:  {doc.get('table_id')}")

    # Caption
    print(f"\nCaption:")
    print(f"   {doc.get('caption', 'Nessuna caption trovata')}")

    # Corpo (Troncato per leggibilità)
    body = doc.get('body_content', '')
    preview_len = 300
    body_preview = " ".join(body[:preview_len].split()) # Rimuove a capo multipli
    print(f"Corpo (Primi {preview_len} caratteri):")
    print(f"   {body_preview}...")

    #  Menzioni (Citazioni esplicite)
    mentions = doc.get('mentions', [])
    print(f"Menzioni esplicite (Trovati {len(mentions)} paragrafi):")
    for i, m in enumerate(mentions[:10], 1): # Ne mostriamo max 10
        print(f"   {i}. \"{m[:100]}...\"")

    # Contesto (Keywords matching)
    context = doc.get('context_paragraphs', [])
    print(f"Contesto semantico (Trovati {len(context)} paragrafi):")
    for i, c in enumerate(context[:10], 1): # Ne mostriamo max 10
            print(f"   {i}. \"{c[:100]}...\"")

if __name__ == "__main__":
    verify_index_tables()