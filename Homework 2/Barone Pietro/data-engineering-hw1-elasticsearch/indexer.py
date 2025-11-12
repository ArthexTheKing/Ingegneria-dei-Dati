from elasticsearch import Elasticsearch
import os, json, config, time

def index_files():
    """Index all .txt files and save token analysis in JSON format."""

    es = Elasticsearch(config.ELASTIC_URL)

    # Delete the index if it already exists
    if es.indices.exists(index=config.INDEX_NAME):
        es.indices.delete(index=config.INDEX_NAME)
        print(f"\nDeleted existing index '{config.INDEX_NAME}'.")

    # Create mapping
    mapping = {
        "mappings": {
            "properties": {
                "nome": {"type": "keyword"},
                "contenuto": {"type": "text", "analyzer": "italian"}
            }
        }
    }

    # Create the index
    start_time = time.time() # Start time measurement
    es.indices.create(index=config.INDEX_NAME, body=mapping)
    print(f"\nIndex '{config.INDEX_NAME}' created successfully.\n")

    results = {}  # Dictionary to store all token results

    # Index all files in the folder
    for filename in os.listdir(config.TXT_FOLDER):
        if not filename.endswith(".txt"):
            continue

        filepath = os.path.join(config.TXT_FOLDER, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Index the document
        es.index(index=config.INDEX_NAME, document={"nome": filename, "contenuto": content})

        # Token analysis for filename
        analysis_filename = es.indices.analyze(
            index=config.INDEX_NAME,
            body={"field": "nome", "text": filename}
        )
        tokens_filename = [t["token"] for t in analysis_filename["tokens"]]

        # Token analysis for content
        analysis_content = es.indices.analyze(
            index=config.INDEX_NAME,
            body={"field": "contenuto", "text": content}
        )
        tokens_content = [t["token"] for t in analysis_content["tokens"]]

        # Add to results dictionary
        results[filename] = {
            "nome": tokens_filename,
            "contenuto": tokens_content
        }

        print(f"Indexed {filename}")
    
    elapsed_time = time.time() - start_time # End time measurement

    # Add total time to JSON
    results["_meta"] = {
        "indexing_time_sec": round(elapsed_time, 3)
    }

    # Save to JSON (overwrite if exists)
    with open(config.OUTPUT_FILE+".json", "w", encoding="utf-8") as out:
        json.dump(results, out, indent=4, ensure_ascii=False)

    print(f"\nIndexing completed in {elapsed_time:.3f} seconds.")
    print(f"Token results saved to {config.OUTPUT_FILE}.json\n")

# Allow direct execution from terminal
if __name__ == "__main__":
    index_files()