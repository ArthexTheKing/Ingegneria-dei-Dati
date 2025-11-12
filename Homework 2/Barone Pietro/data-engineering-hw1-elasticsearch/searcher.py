from elasticsearch import Elasticsearch
import config

def search_files():
    """Performs interactive searches on the Elasticsearch index.""" 

    es = Elasticsearch(config.ELASTIC_URL)

    if not es.indices.exists(index=config.INDEX_NAME):
        print(f"The index '{config.INDEX_NAME}' does not exist. Please run the indexer first.")
        return
    
    print("\nEnter a query in the format:")
    print("- nome:document1")
    print('- contenuto:"phrase"')
    print("- contenuto:word\n")

    while True:
        query_str = input("Query (press Enter to exit): ").strip()
        if not query_str:
            print("Exiting search\n")
            break

        if query_str.startswith("nome:"):
            term = query_str[len("nome:"):].strip()
            query = {"term": {"nome": term}}

        elif query_str.startswith("contenuto:"):
            term = query_str[len("contenuto:"):].strip()

            # Phrase query if enclosed in quotes
            if term.startswith('"') and term.endswith('"'):
                phrase = term.strip('"')
                query = {"match_phrase": {"contenuto": phrase}}
            else:
                query = {"match": {"contenuto": term}}

        else:
            print("\nInvalid syntax. Use nome:document1 or contenuto:word or contenuto:\"phrase\"\n\n")
            continue

        res = es.search(index=config.INDEX_NAME, query=query, size=config.N_MAX_RESULTS, sort=[{"_score": {"order": "desc"}}])

        n_hits = res['hits']['total']['value']
        if n_hits == 0:
            print("\nNo results found")
        else:
            print(f"\nFound {res['hits']['total']['value']} results:")

        for i, hit in enumerate(res["hits"]["hits"], start=1):
            src = hit["_source"]
            contenuto_preview = src.get("contenuto", "")[:config.N_CHARS_PREVIEW].replace("\n", " ")  # Preview
            print(f"{i}. {src['nome']} (score={hit['_score']:.2f})")
            print(f"    Preview: {contenuto_preview}...")
        print("\n")  # Newline for readability

# Allows direct execution from terminal
if __name__ == "__main__":
    search_files()