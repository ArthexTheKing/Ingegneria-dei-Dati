# indexer.py
from elasticsearch import Elasticsearch

def setup_index(es_client, index_name):
    """
    Configura l'indice.
    NOTA: Se l'indice esiste, lo CANCELLA e lo ricrea (Reset).
    """
    if es_client.indices.exists(index=index_name):
        print(f"L'indice '{index_name}' esiste. Eliminazione in corso per reset...")
        es_client.indices.delete(index=index_name)
    
    index_body = {
        
        "mappings": {
            "properties": {
                "arxiv_id": {"type": "keyword"},
                
                # per titolo 'english' (Stemming + Stopwords)
                "title": {
                    "type": "text", 
                    "analyzer": "english" 
                },
                
                # abstract 'english'
                "abstract": {
                    "type": "text", 
                    "analyzer": "english"
                },
                
                # full_text 'english' (Il testo arriva già pulito)
                "full_text": {
                    "type": "text", 
                    "analyzer": "english"
                },
                
                # Autori usiamo 'standard' per non fare stemming
                "authors": {
                    "type": "text",
                    "analyzer": "standard", 
                    "fields": {"raw": {"type": "keyword"}}
                },
                
                "date": {"type": "date"},
                "pdf_url": {"type": "keyword"},
                "local_file_saved": {"type": "boolean"}
            }
        }
    }

    es_client.indices.create(index=index_name, body=index_body)
    print(f"Nuovo indice '{index_name}' creato (Porta 9200).")