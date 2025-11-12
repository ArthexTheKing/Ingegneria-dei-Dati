from elasticsearch import Elasticsearch, helpers
from datasets import load_dataset
import pandas as pd
import time, statistics, config

# Create index with mapping
def create_index(es):
    """Creates the index with mapping."""
    mapping = {
        "mappings": {
            "properties": {
                "nome": {"type": "keyword"},
                "contenuto": {"type": "text", "analyzer": "standard"}
            }
        }
    }

    # Delete existing index if present
    if es.indices.exists(index=config.INDEX_NAME):
        es.indices.delete(index=config.INDEX_NAME)

    # Create the index
    es.indices.create(index=config.INDEX_NAME, body=mapping)

# Bulk indexing function
def bulk_index(es, df: pd.DataFrame):
    """Indexes a DataFrame in bulk mode."""
    actions = []
    for _, row in df.iterrows():
        doc = {'nome': row['book_title'], 'contenuto': row['reader_review']}
        actions.append({"_index": config.INDEX_NAME, "_source": doc})
    helpers.bulk(es, actions)
    es.indices.refresh(index=config.INDEX_NAME) # Refresh index to make documents searchable

# Single document indexing function
def single_index(es, df: pd.DataFrame):
    """Indexes a DataFrame document by document."""
    for _, row in df.iterrows():
        doc = {'nome': row['book_title'], 'contenuto': row['reader_review']}
        es.index(index=config.INDEX_NAME, document=doc)
    es.indices.refresh(index=config.INDEX_NAME) # Refresh index to make documents searchable

# Run a specific mode multiple times and record times
def run_mode(es, df: pd.DataFrame, mode_func, mode_name, num_runs=10):
    times = []
    print(f"\nStarting experiment: {mode_name}")
    for i in range(num_runs):
        create_index(es)
        start = time.time()
        mode_func(es, df)
        elapsed = time.time() - start
        times.append(elapsed)
        count = es.count(index=config.INDEX_NAME)['count']
        print(f"Run {i+1}/{num_runs} - Documents indexed: {count}, Time: {elapsed:.3f}s")
        es.indices.delete(index=config.INDEX_NAME)
    median_time = statistics.median(times)
    print(f"\nResults {mode_name}")
    print(f"Times: {[round(t, 3) for t in times]}")
    print(f"Median time: {median_time:.3f} seconds\n")
    return median_time

def run_benchmark(num_runs=10):
    es = Elasticsearch(config.ELASTIC_URL)
    
    # Load Hugging Face dataset and convert to DataFrame
    ds = load_dataset("Abirate/french_book_reviews", split="train")
    df = pd.DataFrame(ds).head(4600)  # Use only first 4600 records for testing

    median_bulk = run_mode(es, df, bulk_index, "Bulk Indexing", num_runs)
    median_single = run_mode(es, df, single_index, "Single Indexing", num_runs)

    print("Final Comparison")
    print(f"Bulk Median: {median_bulk:.3f} s")
    print(f"Single Median: {median_single:.3f} s")

if __name__ == "__main__":
    run_benchmark()