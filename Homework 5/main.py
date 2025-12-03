from content_retriever import retrive_content
from tables_retriever import index_tables
from figures_retriever import index_figures
from config import inizialize_es


def main():
    
    es = inizialize_es()

    # Setup Indice Contenuti
    retrive_content(es)

    # Setup Indice Tabelle
    index_tables(es)

    # Setup Indice Figure
    index_figures(es)

if __name__ == "__main__":
    main()