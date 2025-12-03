from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
import numpy as np
from config import TFIDF_THRESHOLD, clean_text

# Stopwords estese per le tabelle
CUSTOM_STOPWORDS = list(ENGLISH_STOP_WORDS.union([
    "table", "tables", "figure", "figures", "fig", "figs", 
    "shown", "show", "shows", "showing", "presented", "presents",
    "result", "results", "data", "using", "used", "based", 
    "column", "row", "section", "eq", "equation", "al", "et"
]))


def parse_html_tables(html_content, paper_id):
    """
    Estrae tabelle, caption e contesto (TF-IDF).
    """
    soup = BeautifulSoup(html_content, "html.parser")
    extracted_tables = []
    
    # prepara tutti i paragrafi
    all_paragraphs = soup.find_all("p")
    if not all_paragraphs:
        return []

    # pulisce il testo dei paragrafi
    para_texts = [clean_text(p.get_text()) for p in all_paragraphs]
    
    # Se il paper è troppo corto, usciamo
    if len(para_texts) < 3: return []

    # calcolo TF-IDF con nostre stopwords
    vectorizer = TfidfVectorizer(stop_words=CUSTOM_STOPWORDS)
    
    try:
        tfidf_matrix = vectorizer.fit_transform(para_texts)
    except ValueError:
        return [] # se il testo è vuoto o contiene SOLO stopword


    # Estrazione delle tabelle
    tables = soup.find_all("figure", class_="ltx_table")

    for table in tables:
        table_id = table.get("id", "unknown")
        
        # Caption
        caption_tag = table.find("figcaption")
        caption_text = clean_text(caption_tag.get_text()) if caption_tag else ""
        
        # Body
        real_table = table.find("table")
        body_text = ""
        if real_table:
            body_text = clean_text(real_table.get_text(separator=" "))
        
        # Menzioni (Link espliciti)
        mentions = [] # testo paragraphs che menzionano la tabella
        target_ref = f"#{table_id}" # id della tabella da cercare
        mention_indices = set() #indici dei paragrafi trovati (Se questo paragrafo è già una menzione non considerarlo anche come 'contesto semantico' per evitare duplicati)

        for i, p_tag in enumerate(all_paragraphs):
            links = p_tag.find_all("a", href=True) # tutti tag <a>
            for link in links:
                if link['href'].endswith(target_ref): # vedi se hfref punta alla tabella
                    mentions.append(para_texts[i])
                    mention_indices.add(i)
                    break
        
        # Contesto Semantico (TF-IDF Similarity)
        context_paragraphs = []
        table_query = caption_text + " " + body_text
        
        if table_query.strip():
            # Trasformiamo la tabella in vettore usando le stesse stopwords
            table_vector = vectorizer.transform([table_query])
            
            # Calcolo similarità
            similarities = cosine_similarity(table_vector, tfidf_matrix).flatten()
            
            # Soglia: 0.15 è un buon bilanciamento
            THRESHOLD = 0.20
            relevant_indices = np.where(similarities > THRESHOLD)[0]
            
            for idx in relevant_indices:
                if idx not in mention_indices:
                    context_paragraphs.append(para_texts[idx])

        # Output Doc
        doc = {
            "paper_id": paper_id,
            "table_id": table_id,
            "caption": caption_text,
            "body_content": body_text,
            "mentions": mentions,
            "context_paragraphs": context_paragraphs
        }
        extracted_tables.append(doc)
        
    return extracted_tables