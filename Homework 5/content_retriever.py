import arxiv
import requests
import time
from datetime import datetime
import os
import shutil
import re
import pandas as pd
from elasticsearch import helpers
from bs4 import BeautifulSoup
from config import *
import xml.etree.ElementTree as ET

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

def clean_html_to_text(html_content):
    if not html_content:
        return ""
    
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Rimuove script, stili, head, meta (Standard)
    for element in soup(["script", "style", "head", "meta", "noscript", "iframe"]):
        element.extract()

    # Rimuove l'Abstract dall'HTML
    abstract_div = soup.find("div", class_="ltx_abstract")
    if abstract_div:
        abstract_div.extract() # Lo cancella dall'albero HTML
    
    # Estrae il testo rimanente
    text = soup.get_text(separator=' ')
    
    return " ".join(text.split())

def bulk_index(es_client, df):

    print(f"Indicizzazione bulk di {len(df)} documenti...")
    actions = [
        {"_index": INDEX_CONTENT_NAME, "_id": rec["document_id"], "_source": rec}
        for rec in df.to_dict(orient='records')
    ]

    try:
        success, errors = helpers.bulk(es_client, actions)
        es_client.indices.refresh(index=INDEX_CONTENT_NAME)
        print(f"Completato: {success} documenti indicizzati")
        if errors:
            print(f"Errori: {errors}\n\n")
    except Exception as e:
        print(f"Errore bulk: {e}\n\n")


def download_html_arxiv(es_client):

    client = arxiv.Client()
    search = arxiv.Search(
        query=f'ti:"{SEARCH_QUERY_ARXIV}"',
        max_results=MAX_DOCS,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    
    results = list(client.results(search))

    print(f"\nRicerca: '{SEARCH_QUERY_ARXIV}' - Trovati: {len(results)} articoli.")
    headers = {'User-Agent': USERAGENT_ARXIV}
    data_buffer = []

    for i, result in enumerate(results, 1):
        doc_id = result.entry_id.split("/")[-1]
        safe_title = sanitize_filename(doc_id)
        print(f"[{i}/{len(results)}] Processando: {safe_title}...")

        # Download HTML
        html_url = result.entry_id.replace("/abs/", "/html/")
        raw_html_content = ""
        file_saved = False
        
        
        try:
            resp = requests.get(html_url, headers=headers, timeout=10)
            if resp.status_code == 200 and len(resp.content) > 4096:
                raw_html_content = resp.text
                
                # Salvataggio RAW su disco (Backup)
                file_path = os.path.join(OUTPUT_DIR_ARXIV, f"{safe_title}.html")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(raw_html_content)
                file_saved = True
            else:
                print("      HTML non valido o troppo piccolo (uso abstract come fallback)")
        except Exception as e:
            print(f"      Errore download: {e}")

        # Pulizia testo (BeautifulSoup)
        cleaned_text = ""
        if raw_html_content:
            cleaned_text = clean_html_to_text(raw_html_content)
        else:
            cleaned_text = result.summary # Fallback (ci metti l'abstract)


        # Preparazione dati
        row = {
            "source": "arxiv",
            "document_id": doc_id,
            "title": result.title,
            "authors": [a.name for a in result.authors],
            "date": result.published,
            "abstract": result.summary,
            "full_text": cleaned_text,
            "pdf_url": html_url,
            "local_file_saved": file_saved
        }
        
        data_buffer.append(row)
        time.sleep(3) # Rispetto policy arXiv

    # Bulk indexing
    if not data_buffer:
        print("Nessun dato da indicizzare.")
        return

    df = pd.DataFrame(data_buffer)

    bulk_index(es_client, df)
    
    # Dump CSV (senza il testo completo per non renderlo gigante)
    csv_path = os.path.join(OUTPUT_DIR_ARXIV, METADATA_CSV_ARXIV)
    df.drop(columns=["full_text"]).to_csv(csv_path, index=False)
    print(f"Metadata salvati in CSV: {csv_path}\n")



def download_html_pubmed(es_client):
    pmc_base_url = "https://pmc.ncbi.nlm.nih.gov/articles/"
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    data_buffer = [] # Buffer per bulk indexing


    # Cerca gli ID
    params = {
        "db": "pmc",
        "term": SEARCH_QUERY_PUBMED,
        "retmode": "json",
        "retmax": MAX_DOCS,
        "sort": "relevance"
    }

    pmc_id_list = []
    try:
        response = requests.get(search_url, params=params) # Effettua la ricerca con l'API
        response.raise_for_status() # Lancia ecception per errori HTTP
        data = response.json()
        pmc_id_list = data.get("esearchresult", {}).get("idlist", []) # Estrae gli ID
    except requests.exceptions.RequestException as e:
        print(f"Errore nella ricerca iniziale: {e}")
        return

    print(f"\nRicerca completata. Trovati: {len(pmc_id_list)} articoli.")

    # Ciclo per ogni ID trovato (esempio: 1234567)
    for i, pmcid in enumerate(pmc_id_list, 1):

        saved_local = False
        
        # Creazione URL Articolo
        var_article_url = f"{pmc_base_url}PMC{pmcid}/"
        var_article_id = f"PMC{pmcid}"
        
        print(f"[{i}/{len(pmc_id_list)}] Processando: {var_article_id}...")

        # Download HTML
        headers = {'User-Agent': USERAGENT_PUBMED}
        try:
            r = requests.get(var_article_url, headers=headers)
            if r.status_code == 200 and len(r.content) > 4096: # se non troppo piccolo e OK

                # Salvataggio su disco
                fname = f"{var_article_id}.html"
                fpath = os.path.join(OUTPUT_DIR_PUBMED, fname)
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(r.text)
                    saved_local = True
            else:
                print(f"    Attenzione: HTML non valido per {var_article_id}")
        except Exception as e:
            print(f"    Errore download HTML: {e}")


        # Recupero Metadati Completi (Titolo, Autori, Abstract)
        meta_params = {
            "db": "pmc",
            "id": pmcid,
            "retmode": "xml"
        }

        var_authors = []
       
        try:
            meta_resp = requests.get(fetch_url, params=meta_params) # XML documento (con tutto)
            meta_resp.raise_for_status() # Lancia eccezione per errori HTTP
            
            root = ET.fromstring(meta_resp.content) # Radice dell'XML
            
            # Estrazione Titolo
            title_node = root.find(".//article-title")
            if title_node is not None:
                var_title = "".join(title_node.itertext()).strip() # itertext() serve per prendere tutto il testo pulito dai tag interni

            # Estrazione Abstract
            abstract_node = root.find(".//abstract")

            if abstract_node is not None:
                # cerca solo i figli diretti title del nodo abstract per ignorare <title> annidati dentro <sec> o altre strutture.
                for direct_title in abstract_node.findall("title"):
                    direct_title.text = ""  # Svuotiamo il testo interno del titolo

                # Estraiamo tutto il resto
                raw_abstract = " ".join(abstract_node.itertext()) # Estrae tutti i frammenti di testo dai sotto-tag
                var_abstract = " ".join(raw_abstract.split()) # spezza la stringa su spazi bianchi e ricompone
            else:
                var_abstract = ""

            # Estrazione Autori Completi (nel gruppo contributori)
            for contrib in root.findall(".//contrib"):
                if contrib.get("contrib-type") == "author": # cerco nodo contrib con attributo contrib-type="author"
                    name_node = contrib.find("name") # dentro contrib cerco nodo name
                    if name_node is not None:
                        surname = name_node.find("surname")
                        given = name_node.find("given-names")
                        
                        s_text = surname.text if surname is not None else ""
                        g_text = given.text if given is not None else ""
                        
                        full_name = f"{g_text} {s_text}".strip() # strip per rimuovere spazi inutili
                        if full_name:
                            var_authors.append(full_name)

            # Estrazione Data (Priorità: epub -> pub -> Default 1970)
            target_date_node = None
            
            # Cerchiamo prima 'epub'
            for node in root.findall(".//pub-date"): # nodo pub-date
                if node.get("pub-type") == "epub": # nodo pub-date con attributo pub-type="epub"
                    target_date_node = node
                    break
            
            # Se non c'è 'epub', cerchiamo 'pub'
            if target_date_node is None:
                for node in root.findall(".//pub-date"): # nodo pub-date
                    if node.get("date-type") == "pub": # nodo pub-date con attributo date-type="pub"
                        target_date_node = node
                        break
            
            # Estrazione Valori (con Default)
            y_int = 1970
            m_int = 1
            d_int = 1

            if target_date_node is not None:
                year_node = target_date_node.find("year")
                month_node = target_date_node.find("month")
                day_node = target_date_node.find("day")
                
                # Se anno c'è sostituisco il default
                if year_node is not None and year_node.text and year_node.text.strip().isdigit():
                    y_int = int(year_node.text.strip())
                
                # Se mese c'è sostituisco il default (gestisce sia numeri "05" che testo "May" se necessario, qui assumiamo numeri)
                if month_node is not None and month_node.text and month_node.text.strip().isdigit():
                    try:
                        m_int = int(month_node.text.strip())
                    except ValueError:
                        m_int = 1
                
                # Se giorno c'è sostituisco il default
                if day_node is not None and day_node.text and day_node.text.strip().isdigit():
                    try:
                        d_int = int(day_node.text.strip())
                    except ValueError:
                        d_int = 1

            # Creazione Oggetto Datetime
            try:
                var_pub_date = datetime(year=y_int, month=m_int, day=d_int)
            except ValueError as e:
                # Caso raro: data impossibile (es. 30 Febbraio), fallback al default
                print(f"    Data non valida recuperata ({y_int}-{m_int}-{d_int}), uso default 1970.")
                var_pub_date = datetime(1970, 1, 1)


            # Estrazione Full Text (nodo body)
            body_node = root.find(".//body")
            if body_node is not None:
                # itertext() estrae testo da paragrafi, sezioni, titoli, tabelle dentro il body
                # Usiamo " " come separatore per evitare che le parole si incollino
                text_content = " ".join(body_node.itertext())
                
                # Pulizia base: rimuove spazi multipli e spazi a inizio/fine
                var_full_text = " ".join(text_content.split())
            else:
                var_full_text = "" # Body non trovato (può capitare se non è open access completo)

        except Exception as e:
            print(f"    Errore recupero metadati XML: {e}")        

        row = {
            "source": "pubmed",
            "document_id": var_article_id,
            "title": var_title,
            "authors": var_authors,
            "full_text": var_full_text,
            "date": var_pub_date,
            "abstract": var_abstract,
            "pdf_url": var_article_url,
            "local_file_saved": saved_local
        }

        data_buffer.append(row)
        
        
        # Pausa obbligatoria anti-ban
        time.sleep(2.0)
    
    # Bulk indexing
    if not data_buffer:
        print("Nessun dato da indicizzare.")
        return

    df = pd.DataFrame(data_buffer)

    bulk_index(es_client, df)

    # Dump CSV (senza il testo completo per non renderlo gigante)
    csv_path = os.path.join(OUTPUT_DIR_PUBMED, METADATA_CSV_PUBMED)
    df.drop(columns=["full_text"]).to_csv(csv_path, index=False)
    print(f"Metadata salvati in CSV: {csv_path}\n")

    
   


def retrive_content(es_client):

    # Setup (Cancella e ricrea indice)
    setup_content_index(es_client)

    # Prepara cartella output (cancella se esiste)
    prepare_output_folder(OUTPUT_DIR_ARXIV)
    prepare_output_folder(OUTPUT_DIR_PUBMED)

    download_html_arxiv(es_client)
    download_html_pubmed(es_client)


# Configura l'indice. Se l'indice esiste, lo cancella e lo ricrea
def setup_content_index(es_client):
    if es_client.indices.exists(index=INDEX_CONTENT_NAME):
        print(f"L'indice '{INDEX_CONTENT_NAME}' esiste. Eliminazione in corso...")
        es_client.indices.delete(index=INDEX_CONTENT_NAME)
    
    index_body = {
        
        "mappings": {
            "properties": {
                "source": {"type": "keyword"}, # arxiv o pubmed
                "document_id": {"type": "keyword"},
                
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