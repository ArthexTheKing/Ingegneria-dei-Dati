from config import inizialize_es, INDEX_FIGURES_NAME

def verify_index_figures():

    es = inizialize_es()

    # Controllo conteggio totale
    count = es.count(index=INDEX_FIGURES_NAME)['count']
    print(f"Totale figure nell'indice '{INDEX_FIGURES_NAME}': {count}\n")

    # Recupero di un documento a caso (usiamo una query match_all con size 1)
    resp = es.search(index=INDEX_FIGURES_NAME, body={"query": {"match_all": {}}, "size": 1})
    
    if not resp['hits']['hits']:
        print("Indice vuoto.")
        return

    doc = resp['hits']['hits'][0]['_source']

    print(f"Figure ID: {doc.get('figure_id')} (Paper: {doc.get('paper_id')})") # Identificativi
    print(f"URL: {doc.get('img_url')}") # URL immagine
    print(f"Caption: {doc.get('caption')}\n") # Caption
    
    
    #  Menzioni (Citazioni esplicite)
    mentions = doc.get('mentions', [])
    print(f"Menzioni ({len(mentions)}):")
    for i, m in enumerate(mentions[:10], 1): # Ne mostriamo max 10
            print(f"   {i}. \"{m[:100]}...\"")
    
    # Contesto (Keywords matching)
    context = doc.get('context_paragraphs', [])
    print(f"Contesto ({len(context)}):")
    for i, c in enumerate(context[:10], 1): # Ne mostriamo max 10
            print(f"   {i}. \"{c[:100]}...\"")

if __name__ == "__main__":
    verify_index_figures()