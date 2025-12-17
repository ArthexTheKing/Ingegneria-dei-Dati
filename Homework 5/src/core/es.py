from elasticsearch import Elasticsearch, ConnectionError
from src.config import Config

def get_es_client():
    """
    Restituisce il client Elasticsearch.
    Solleva ConnectionError se la connessione fallisce.
    """
    es = Elasticsearch(Config.ES_HOST)
    
    # Ping immediato per verificare la connettività reale
    if not es.ping():
        raise ConnectionError(f"Impossibile connettersi a Elasticsearch su {Config.ES_HOST}")
    
    return es