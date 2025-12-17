import arxiv
import requests
import time
import os
import pandas as pd
from bs4 import BeautifulSoup
from src.config import Config
from src.core.utils import clean_text, sanitize_filename

def download_arxiv_data():
    """Scarica metadati e HTML da ArXiv."""
    print(f"\n[ArXiv] Ricerca: '{Config.QUERY_ARXIV}'")
    
    client = arxiv.Client()
    search = arxiv.Search(
        query=f'ti:"{Config.QUERY_ARXIV}"',
        max_results=Config.MAX_DOCS,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    
    results = list(client.results(search))
    data_buffer = []

    if not os.path.exists(Config.OUTPUT_DIR_ARXIV):
        os.makedirs(Config.OUTPUT_DIR_ARXIV)

    for i, result in enumerate(results, 1):
        doc_id = result.entry_id.split("/")[-1]
        safe_title = sanitize_filename(doc_id)
        
        print(f"[{i}/{len(results)}] ArXiv Processing: {doc_id}")

        # Download HTML
        html_url = result.entry_id.replace("/abs/", "/html/")
        raw_html = ""
        file_saved = False
        
        try:
            resp = requests.get(html_url, headers={'User-Agent': Config.USERAGENT_ARXIV}, timeout=15)
            if resp.status_code == 200 and len(resp.content) > 2000:
                raw_html = resp.text
                # Salvataggio su file
                file_path = os.path.join(Config.OUTPUT_DIR_ARXIV, f"{safe_title}.html")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(raw_html)
                file_saved = True
        except Exception as e:
            print(f"   Errore download HTML: {e}")

        # Pulizia testo per full_text index
        cleaned_text = ""
        if raw_html:
            soup = BeautifulSoup(raw_html, "html.parser")
            for tag in soup(["script", "style", "head", "meta"]):
                tag.extract()
            cleaned_text = clean_text(soup.get_text())
        else:
            cleaned_text = result.summary

        data_buffer.append({
            "source": "arxiv",
            "document_id": doc_id,
            "title": result.title,
            "authors": [a.name for a in result.authors],
            "date": result.published,
            "abstract": result.summary,
            "full_text": cleaned_text,
            "pdf_url": html_url,
            "local_file_saved": file_saved,
            "local_filename": f"{safe_title}.html" if file_saved else None
        })
        
        time.sleep(2) # Rate limit

    return pd.DataFrame(data_buffer)