import arxiv
import requests
import time
import os
import shutil
import re
import pandas as pd
from elasticsearch import helpers
from bs4 import BeautifulSoup
from config import inizialize_es, INDEX_CONTENT_NAME, OUTPUT_DIR, SEARCH_QUERY, MAX_DOCS

# Cerca il tag <base href="..."> per trovare l'ID reale del paper.
def get_base_url_from_html(soup, fallback_id=""):
    base_tag = soup.find("base")
    
    if base_tag and base_tag.get("href"):
        relative_path = base_tag.get("href")
        if relative_path.startswith("/"):
            return f"https://arxiv.org{relative_path}"
        else:
            return f"https://arxiv.org/{relative_path}"
    
    return f"https://arxiv.org/html/{fallback_id}/"

def sanitize_filename(title):
    """Pulisce il titolo per il file system."""
    title = title.replace('$', '')
    title = re.sub(r'\\(text|emph|textbf|textit|math[a-z]+)', '', title)
    clean_chars = str.maketrans('', '', '{}[]^\\_')
    title = title.translate(clean_chars)
    title = re.sub(r'[\\/*?:"<>|]', "", title)
    title = " ".join(title.split())
    return title[:150].strip()

def prepare_output_folder(directory):
    if os.path.exists(directory):
        shutil.rmtree(directory)
    os.makedirs(directory)

# Usa BeautifulSoup per trasformare HTML sporco in testo pulito.
def clean_html_to_text(html_content):
    if not html_content:
        return ""
    
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Rimuove script, stili, head, meta
    for element in soup(["script", "style", "head", "meta", "noscript", "iframe"]):
        element.extract()
    
    # Estrae il testo (separator=' ' evita che le parole si incollino)
    text = soup.get_text(separator=' ')
    
    # Rimuove spazi eccessivi
    return " ".join(text.split())

def retrive_content(es_client):

    # Setup (Cancella e ricrea indice)
    setup_content_index(es_client)

    # Prepara cartella output (cancella se esiste)
    prepare_output_folder(OUTPUT_DIR)

    client = arxiv.Client()
    search = arxiv.Search(
        query=f'ti:"{SEARCH_QUERY}"',
        max_results=MAX_DOCS,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    
    results = list(client.results(search))
    print(f"\nRicerca: '{SEARCH_QUERY}' - Trovati: {len(results)} articoli.\n")
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    data_buffer = []

    for i, result in enumerate(results, 1):
        doc_id = result.entry_id.split("/")[-1]
        safe_title = sanitize_filename(result.title)
        print(f"[{i}/{len(results)}] Processando: {safe_title[:40]}...")

        # Download HTML
        html_url = result.entry_id.replace("/abs/", "/html/")
        raw_html_content = ""
        file_saved = False
        
        try:
            resp = requests.get(html_url, headers=headers, timeout=10)
            if resp.status_code == 200 and len(resp.content) > 4096:
                raw_html_content = resp.text
                
                # Salvataggio RAW su disco (Backup)
                file_path = os.path.join(OUTPUT_DIR, f"{safe_title}.html")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(raw_html_content)
                file_saved = True
            else:
                print(html_url)
                print("      HTML non valido o troppo piccolo.")
        except Exception as e:
            print(f"      Errore download: {e}")

        # Pulizia testo (BeautifulSoup)
        cleaned_text = ""
        if raw_html_content:
            cleaned_text = clean_html_to_text(raw_html_content)
        else:
            cleaned_text = result.summary # Fallback

        # Preparazione dati
        row = {
            "arxiv_id": doc_id,
            "title": result.title,
            "authors": [a.name for a in result.authors],
            "date": result.published,
            "abstract": result.summary,
            "full_text": cleaned_text,
            "pdf_url": result.pdf_url,
            "local_file_saved": file_saved
        }
        
        data_buffer.append(row)
        time.sleep(3) # Rispetto policy arXiv

    # Bulk indexing
    if not data_buffer:
        print("Nessun dato da indicizzare.")
        return

    df = pd.DataFrame(data_buffer)
    
    # Dump CSV (senza il testo completo per non renderlo gigante)
    csv_path = os.path.join(OUTPUT_DIR, "_metadata.csv")
    df.drop(columns=["full_text"]).to_csv(csv_path, index=False)
    print(f"\nMetadata salvati in CSV: {csv_path}")

    print(f"Indicizzazione bulk di {len(df)} documenti...")
    actions = [
        {"_index": INDEX_CONTENT_NAME, "_id": rec["arxiv_id"], "_source": rec}
        for rec in df.to_dict(orient='records')
    ]

    try:
        success, errors = helpers.bulk(es_client, actions)
        es_client.indices.refresh(index=INDEX_CONTENT_NAME)
        print(f"Completato: {success} documenti indicizzati\n")
        if errors:
            print(f"Errori: {errors}\n\n")
    except Exception as e:
        print(f"Errore bulk: {e}\n\n")


# Configura l'indice. Se l'indice esiste, lo cancella e lo ricrea
def setup_content_index(es_client):
    if es_client.indices.exists(index=INDEX_CONTENT_NAME):
        print(f"L'indice '{INDEX_CONTENT_NAME}' esiste. Eliminazione in corso...")
        es_client.indices.delete(index=INDEX_CONTENT_NAME)
    
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

    es_client.indices.create(index=INDEX_CONTENT_NAME, body=index_body)
    print(f"Nuovo indice '{INDEX_CONTENT_NAME}' creato")

if __name__ == "__main__":
    es_client = inizialize_es()
    retrive_content(es_client)