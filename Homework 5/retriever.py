import arxiv
import requests
import time
import os
import shutil
import re
import pandas as pd
from elasticsearch import helpers
from bs4 import BeautifulSoup

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

def clean_html_to_text(html_content):
    """
    Usa BeautifulSoup per trasformare HTML sporco in testo pulito.
    """
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

def fetch_and_index_documents(es_client, index_name, query, output_dir, max_results=5):
    
    prepare_output_folder(output_dir)

    client = arxiv.Client()
    search = arxiv.Search(
        query=f'ti:"{query}"',
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    
    results = list(client.results(search))
    print(f"\nRicerca: '{query}' - Trovati: {len(results)} articoli.\n")
    
    headers = {'User-Agent': 'Mozilla/5.0 (Custom Script)'}
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
                file_path = os.path.join(output_dir, f"{safe_title}.html")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(raw_html_content)
                file_saved = True
            else:
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
    csv_path = os.path.join(output_dir, "_metadata.csv")
    df.drop(columns=["full_text"]).to_csv(csv_path, index=False)
    print(f"\nMetadata salvati in CSV: {csv_path}")

    print(f"Indicizzazione bulk di {len(df)} documenti...")
    actions = [
        {"_index": index_name, "_id": rec["arxiv_id"], "_source": rec}
        for rec in df.to_dict(orient='records')
    ]

    try:
        success, errors = helpers.bulk(es_client, actions)
        es_client.indices.refresh(index=index_name)
        print(f"Completato! Documenti indicizzati: {success}")
        if errors: print(f"Errori: {errors}")
    except Exception as e:
        print(f"Errore bulk: {e}")