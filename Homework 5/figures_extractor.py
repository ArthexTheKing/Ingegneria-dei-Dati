import re
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
import numpy as np
from config import TFIDF_THRESHOLD, clean_text
from content_retriever import get_base_url_from_html

# Stopwords estese per le figure
CUSTOM_STOPWORDS = list(ENGLISH_STOP_WORDS.union([
    "figure", "figures", "fig", "figs", "image", "plot", "graph", 
    "shown", "show", "shows", "showing", "see", "refer", 
    "left", "right", "top", "bottom", "middle", "red", "blue", "green", "line"
]))


# Estrae figure, caption, URL e contesto (TF-IDF).
def parse_html_figures(html_content, filename):

    soup = BeautifulSoup(html_content, "html.parser")
    extracted_figures = []

    base_url = get_base_url_from_html(soup, fallback_id=filename)
    
    # Estrae l'ID numerico (es. 2511.11104) dall'URL base
    match_id = re.search(r'/html/([\d\.]+v?\d?)/?', base_url)
    real_arxiv_id = match_id.group(1) if match_id else filename
    
    # Preparazione corpus
    all_paragraphs = soup.find_all("p")
    if not all_paragraphs: return []

    para_texts = [clean_text(p.get_text()) for p in all_paragraphs]
    
    # Se il paper è troppo corto, usciamo
    if len(para_texts) < 3: return []

    # TF-IDF vectorizer
    vectorizer = TfidfVectorizer(stop_words=CUSTOM_STOPWORDS)
    try:
        tfidf_matrix = vectorizer.fit_transform(para_texts)
    except ValueError:
        return []

    # Estrazione figure
    # In arXiv HTML le figure hanno classe "ltx_figure"
    figures = soup.find_all("figure", class_="ltx_figure")

    for fig in figures:
        fig_id = fig.get("id", "unknown")
        
        # Caption
        caption_tag = fig.find("figcaption")
        caption_text = clean_text(caption_tag.get_text()) if caption_tag else ""
        
        # URL Immagine (src)
        img_tag = fig.find("img")
        img_src = ""
        full_url = ""
        if img_tag and img_tag.has_attr('src'):
            img_src = img_tag['src']
            # Ricostruiamo l'URL assoluto per utilità
            full_url = f"{base_url}{img_src}"

        # Menzioni (Link espliciti)
        mentions = []
        target_ref = f"#{fig_id}"
        mention_indices = set()

        for i, p_tag in enumerate(all_paragraphs):
            links = p_tag.find_all("a", href=True)
            for link in links:
                if link['href'].endswith(target_ref):
                    mentions.append(para_texts[i])
                    mention_indices.add(i)
                    break
        
        # Contesto Semantico (TF-IDF Similarity)
        context_paragraphs = []
        
        # Per le figure, la "query" è SOLO la caption (non c'è testo nel corpo)
        fig_query = caption_text
        
        if fig_query.strip():
            query_vector = vectorizer.transform([fig_query])
            similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()
            
            # Soglia TF-IDF come per le tabelle
            relevant_indices = np.where(similarities > TFIDF_THRESHOLD)[0]
            
            for idx in relevant_indices:
                if idx not in mention_indices:
                    context_paragraphs.append(para_texts[idx])

        # Creazione oggetto
        doc = {
            "paper_id": real_arxiv_id,                  # ID numerico (es. 2511.11104)
            "paper_title_slug": filename,               # Nome del file senza estensione
            "figure_id": fig_id,                        # ID HTML della figura. Preso dall'attributo id="..." del tag <figure> (univoco)
            "img_url": full_url,                        # URL assoluto dell'immagine (https://arxiv.org/html/2511.11104v1/figures/dual-biases-v2.png)
            "local_src": img_src,                       # Salva anche il path locale (figures/dual-biases-v2.png)
            "caption": caption_text,                    # Testo della caption
            "mentions": mentions,                       # Paragrafi che menzionano esplicitamente la figura (completi)
            "context_paragraphs": context_paragraphs    # Paragrafi rilevanti per similarità TF-IDF (completi)
        }
        extracted_figures.append(doc)

    return extracted_figures