import requests
import time
import os
import xml.etree.ElementTree as ET
from datetime import datetime
import pandas as pd
from src.config import Config

# --- Helper Functions per parsing sicuro XML ---
def _safe_get_text(element, xpath):
    """
    Cerca un nodo tramite xpath. Se esiste, restituisce tutto il testo contenuto.
    Se non esiste, restituisce stringa vuota.
    """
    if element is None:
        return ""
    node = element.find(xpath)
    if node is None:
        return ""
    # itertext() recupera testo anche dai sotto-tag (es. <i>, <b>)
    return "".join(node.itertext()).strip()

def _safe_get_int(element, xpath, default_val):
    """
    Cerca un nodo tramite xpath e prova a convertirlo in int.
    Gestisce casi di nodo mancante, testo None o conversioni fallite.
    """
    if element is None:
        return default_val
    
    node = element.find(xpath)
    if node is None:
        return default_val
        
    text_val = node.text
    if not text_val: # Gestisce None o stringa vuota
        return default_val
        
    try:
        return int(text_val.strip())
    except ValueError:
        return default_val
# -----------------------------------------------

def download_pubmed_data():
    """Scarica metadati (XML) e HTML da PubMed Central."""
    print(f"\n[PubMed] Ricerca: '{Config.QUERY_PUBMED}'")
    
    base_url = "https://pmc.ncbi.nlm.nih.gov/articles/"
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    
    if not os.path.exists(Config.OUTPUT_DIR_PUBMED):
        os.makedirs(Config.OUTPUT_DIR_PUBMED)

    # 1. Cerca ID
    try:
        resp = requests.get(search_url, params={
            "db": "pmc", 
            "term": Config.QUERY_PUBMED, 
            "retmode": "json", 
            "retmax": Config.MAX_DOCS, 
            "sort": "relevance"
        })
        resp.raise_for_status()
        data = resp.json()
        pmc_ids = data.get("esearchresult", {}).get("idlist", [])
    except Exception as e:
        print(f"Errore ricerca PubMed: {e}")
        return pd.DataFrame()

    data_buffer = []

    # 2. Fetch Dettagli
    for i, pmcid in enumerate(pmc_ids, 1):
        pmc_id_str = f"PMC{pmcid}"
        print(f"[{i}/{len(pmc_ids)}] PubMed Processing: {pmc_id_str}")
        
        # A. Download HTML (per figure/tabelle)
        html_url = f"{base_url}{pmc_id_str}/"
        saved_local = False
        try:
            r = requests.get(html_url, headers={'User-Agent': Config.USERAGENT_PUBMED})
            if r.status_code == 200 and len(r.content) > 4000:
                fname = f"{pmc_id_str}.html"
                with open(os.path.join(Config.OUTPUT_DIR_PUBMED, fname), "w", encoding="utf-8") as f:
                    f.write(r.text)
                saved_local = True
        except Exception:
            pass # Ignoriamo errori HTML per non bloccare il flusso

        # B. Download Metadata via XML
        try:
            meta_resp = requests.get(fetch_url, params={"db": "pmc", "id": pmcid, "retmode": "xml"})
            meta_resp.raise_for_status()
            
            # Parsing dell'XML
            root = ET.fromstring(meta_resp.content)
            
            # 1. Titolo (Sicuro)
            title = _safe_get_text(root, ".//article-title")
            if not title:
                title = "Title Unknown"
            
            # 2. Autori (Sicuro)
            authors = []
            for contrib in root.findall(".//contrib"):
                if contrib.get("contrib-type") == "author":
                    name_node = contrib.find("name")
                    if name_node is not None:
                        s = _safe_get_text(name_node, "surname")
                        g = _safe_get_text(name_node, "given-names")
                        full = f"{g} {s}".strip()
                        if full: authors.append(full)

            # 3. Abstract (Sicuro)
            abstract = ""
            abs_node = root.find(".//abstract")
            if abs_node is not None:
                # Rimuove titoli interni per pulizia (es. "Background", "Methods")
                for t in abs_node.findall("title"): 
                    t.text = "" 
                abstract = "".join(abs_node.itertext()) # itertext su abs_node (non None)
                abstract = " ".join(abstract.split())

            # 4. Data (Sicuro - con logica priorità epub > pub)
            dt = datetime(1970, 1, 1) # Default
            
            date_node = None
            # Cerca data epub
            for node in root.findall(".//pub-date"):
                if node.get("pub-type") == "epub": 
                    date_node = node
                    break
            
            # Se non trova epub, cerca ppub o pub generico
            if date_node is None:
                for node in root.findall(".//pub-date"):
                    if node.get("date-type") == "pub" or node.get("pub-type") == "ppub": 
                        date_node = node
                        break
            
            if date_node is not None:
                # Usa la helper function che gestisce None e errori di conversione
                y = _safe_get_int(date_node, "year", 1970)
                m = _safe_get_int(date_node, "month", 1)
                d = _safe_get_int(date_node, "day", 1)
                try:
                    dt = datetime(y, m, d)
                except ValueError:
                    dt = datetime(1970, 1, 1) # Fallback se data invalida (es. 30 Febbraio)

            # 5. Full Text da XML Body (Sicuro)
            full_text = _safe_get_text(root, ".//body")
            full_text = " ".join(full_text.split())

            # Aggiunta al buffer
            data_buffer.append({
                "source": "pubmed",
                "document_id": pmc_id_str,
                "title": title,
                "authors": authors,
                "date": dt,
                "abstract": abstract,
                "full_text": full_text,
                "pdf_url": html_url,
                "local_file_saved": saved_local,
                "local_filename": f"{pmc_id_str}.html" if saved_local else None
            })

        except Exception as e:
            # Stampa l'errore ma continua con il prossimo paper
            print(f"   Errore parsing XML per {pmc_id_str}: {e}")

        time.sleep(1.0) # Rate limit cortesia

    return pd.DataFrame(data_buffer)