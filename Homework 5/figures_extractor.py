import re
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
import numpy as np
from config import TFIDF_THRESHOLD, clean_text

# Stopwords estese per le figure
CUSTOM_STOPWORDS = list(ENGLISH_STOP_WORDS.union([
    "figure", "figures", "fig", "figs", "image", "plot", "graph", 
    "shown", "show", "shows", "showing", "see", "refer", 
    "left", "right", "top", "bottom", "middle", "red", "blue", "green", "line"
]))


def parse_html_figures(html_content, paper_id):
    """
    Estrae figure, caption, URL e contesto (TF-IDF).
    """
    soup = BeautifulSoup(html_content, "html.parser")
    extracted_figures = []
    
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
            full_url = f"https://arxiv.org/html/{paper_id}/{img_src}"

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
            "paper_id": paper_id,
            "figure_id": fig_id,
            "img_url": full_url,   # Salva l'URL completo
            "local_src": img_src,  # Salva anche il path locale
            "caption": caption_text,
            "mentions": mentions,
            "context_paragraphs": context_paragraphs
        }
        extracted_figures.append(doc)
        
    return extracted_figures