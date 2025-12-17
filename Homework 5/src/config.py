import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Elasticsearch
    ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")
    
    # Indices
    INDEX_DOCS = "content_index"
    INDEX_TABLES = "tables_index"
    INDEX_FIGURES = "figures_index"

    # PubMed Settings
    PUBMED_EMAIL = os.getenv("PUBMED_EMAIL", "example@email.com")
    USERAGENT_PUBMED = f"UniProject_CorpusBuilder/2.0 (contact: {PUBMED_EMAIL})"
    
    # ArXiv Settings
    USERAGENT_ARXIV = "Mozilla/5.0 (Research Project)"
    
    # Paths
    OUTPUT_DIR_ARXIV = os.path.join(os.getcwd(), "data", "arxiv")
    OUTPUT_DIR_PUBMED = os.path.join(os.getcwd(), "data", "pubmed")
    
    # Algorithms
    TFIDF_THRESHOLD = 0.15
    MAX_DOCS = 10

    # Queries
    QUERY_ARXIV = "text to speech"
    QUERY_PUBMED = (
        "(((ultra-processed[Title] AND foods[Title]) OR (ultra-processed[Abstract] AND foods[Abstract])) OR "
        "((cardiovascular[Title] AND risk[Title]) OR (cardiovascular[Abstract] AND risk[Abstract]))) AND "
        "open access[filter]"
    )