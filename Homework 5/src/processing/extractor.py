from bs4 import BeautifulSoup
import re
from src.processing.analyzer import ContextAnalyzer
from src.core.utils import clean_text

def _get_attr_str(tag, attr_name):
    """
    Helper sicuro per ottenere un attributo da un tag BS4 come stringa.
    Gestisce i casi in cui get() restituisce None o una lista (es. classi).
    """
    if not tag:
        return ""
    val = tag.get(attr_name)
    
    if val is None:
        return ""
    if isinstance(val, list):
        return " ".join(val)  # Unisce liste (es. classi multiple)
    return str(val).strip()

def extract_multimedia(html_content, paper_id, source_type):
    """
    Estrae SIA figure CHE tabelle da un file HTML.
    Restituisce due liste: (figures, tables)
    """
    soup = BeautifulSoup(html_content, "html.parser")
    
    # --- FIX BASE URL ---
    base_url = ""
    base_tag = soup.find("base")
    
    # Controllo esplicito prima della concatenazione
    if base_tag and source_type == "arxiv":
        href_val = _get_attr_str(base_tag, "href")
        if href_val:
            base_url = "https://arxiv.org" + href_val

    # Preparazione paragrafi per contesto
    all_p_tags = soup.find_all("p")
    # Filtro paragrafi troppo corti
    valid_p_tags = [p for p in all_p_tags if len(p.get_text()) > 50]
    p_texts = [clean_text(p.get_text()) for p in valid_p_tags]
    
    # Inizializza analizzatore semantico
    analyzer = ContextAnalyzer(p_texts)
    
    figures_data = []
    tables_data = []

    # --- LOGICA TABLE ---
    # Usiamo _get_attr_str che garantisce di restituire una stringa (es. "class1 class2")
    # In questo modo l'operatore 'in' cerca la sottostringa in modo sicuro ed evita errori con None.
    
    table_nodes = soup.find_all(lambda tag: 
        (tag.name == "figure" and "ltx_table" in _get_attr_str(tag, "class")) or 
        (tag.name in ["div", "section"] and "table-wrap" in _get_attr_str(tag, "class"))
    )

    for tbl in table_nodes:
        t_id = _get_attr_str(tbl, "id") or "unknown"
        
        # Caption Logic (Alternativa con CSS Selectors)
        caption = ""
        # Cerca un figcaption O un div che abbia "caption" nella classe
        # [class*="caption"] significa "la classe contiene la parola caption"
        cap_tag = tbl.select_one("figcaption[class*='caption'], div[class*='caption']")
        
        if cap_tag: 
            caption = clean_text(cap_tag.get_text())
        
        # Body Logic
        body_content = ""
        real_tbl = tbl.find("table")
        if real_tbl: 
            # separator=" " evita che le celle si incollino
            body_content = clean_text(real_tbl.get_text(separator=" "))
        
        # Mentions Logic
        mentions, mention_idxs = _find_mentions(valid_p_tags, p_texts, t_id)
        
        # Context Logic
        context = analyzer.find_context(caption + " " + body_content, exclude_indices=mention_idxs)
        
        # Salviamo solo se c'è almeno un contenuto utile
        if caption or body_content:
            tables_data.append({
                "source": source_type,
                "paper_id": paper_id,
                "table_id": t_id,
                "caption": caption,
                "body_content": body_content,
                "mentions": mentions,
                "context_paragraphs": context
            })

    # --- LOGICA FIGURE ---
    # --- LOGICA FIGURE ---
    fig_nodes = soup.find_all("figure")
    
    # FIX: Usa _get_attr_str(f, "class") invece di f.get("class", [])
    # _get_attr_str restituisce sempre una stringa sicura (es. "ltx_figure ltx_table"),
    # quindi l'operatore "not in" funziona perfettamente senza errori di tipo.
    fig_nodes = [f for f in fig_nodes if "ltx_table" not in _get_attr_str(f, "class")]
    for fig in fig_nodes:
        f_id = _get_attr_str(fig, "id") or "unknown"
        
        # Caption
        caption = ""
        cap_tag = fig.find("figcaption")
        if cap_tag: 
            caption = clean_text(cap_tag.get_text())

        # Img URL
        img_url = ""
        img_tag = fig.find("img")
        
        if img_tag:
            # --- FIX SRC ATTRIBUTE ---
            src = _get_attr_str(img_tag, "src")
            
            if src:
                if src.startswith("http"): 
                    img_url = src
                elif base_url: 
                    # ArXiv usa il base_url estratto prima
                    img_url = f"{base_url}{src}"
                elif source_type == "pubmed" and not src.startswith("http"):
                    # PubMed relative logic
                    img_url = f"https://pmc.ncbi.nlm.nih.gov{src}"

        # Mentions & Context
        mentions, mention_idxs = _find_mentions(valid_p_tags, p_texts, f_id)
        context = analyzer.find_context(caption, exclude_indices=mention_idxs)

        if img_url or caption:
            figures_data.append({
                "source": source_type,
                "paper_id": paper_id,
                "figure_id": f_id,
                "img_url": img_url,
                "caption": caption,
                "mentions": mentions,
                "context_paragraphs": context
            })

    return figures_data, tables_data

def _find_mentions(p_tags, p_texts, target_id):
    """Trova menzioni esplicite (link href) nei paragrafi."""
    mentions = []
    indices = set()
    ref_link = f"#{target_id}"
    
    for i, p in enumerate(p_tags):
        # Cerca link interni
        links = p.find_all("a", href=True)
        for link in links:
            # Anche qui href potrebbe essere None teoricamente, ma href=True nel find lo filtra parzialmente.
            # Per sicurezza usiamo la stringa diretta.
            href_val = str(link['href']) 
            if href_val.endswith(ref_link):
                mentions.append(p_texts[i])
                indices.add(i)
                break 
    return mentions, indices