from bs4 import BeautifulSoup
import re
from src.processing.analyzer import ContextAnalyzer
from src.core.utils import clean_text
import time   # <-- [AGGIUNTO] per misurazione tempi


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
        return " ".join(val)
    return str(val).strip()


def _find_mentions(p_tags, p_texts, target_id):
    """
    Trova menzioni esplicite (link href) nei paragrafi.
    Restituisce: (lista_testi_menzioni, set_indici_menzioni)
    """
    mentions = []
    indices = set()
    ref_link = f"#{target_id}"
    
    for i, p in enumerate(p_tags):
        links = p.find_all("a", href=True)
        for link in links:
            href_val = str(link['href']) 
            if href_val.endswith(ref_link):
                mentions.append(p_texts[i])
                indices.add(i)
                break 
    return mentions, indices


def extract_multimedia(html_content, paper_id, source_type):
    """
    Funzione Entry Point.
    Estrae figure e tabelle smistando la logica in base alla source (arxiv/pubmed).
    """

    # --------------------------------------------------
    # [AGGIUNTO] TIMER 1: Parsing HTML
    # --------------------------------------------------
    t_parse = time.time()
    soup = BeautifulSoup(html_content, "html.parser")
    parsing_time = time.time() - t_parse

    # Preparazione Comune (Estrai i paragrafi validi)
    all_p_tags = soup.find_all("p")

    # Filtro paragrafi troppo corti (es. metadati, link navigazione)
    valid_p_tags = [p for p in all_p_tags if len(p.get_text()) > 50]
    p_texts = [clean_text(p.get_text()) for p in valid_p_tags]
    
    # --------------------------------------------------
    # [AGGIUNTO] TIMER 2: Calcolo TF-IDF
    # --------------------------------------------------
    t_tfidf = time.time()
    analyzer = ContextAnalyzer(p_texts)
    tfidf_time = time.time() - t_tfidf

    # --------------------------------------------------
    # [AGGIUNTO] TIMER 3: Estrazione Multimedia
    # --------------------------------------------------
    t_extract = time.time()

    # Branching Logica
    if source_type == "arxiv":
        figures, tables = _extract_arxiv(
            soup, paper_id, analyzer, valid_p_tags, p_texts
        )
    elif source_type == "pubmed":
        figures, tables = _extract_pubmed(
            soup, paper_id, analyzer, valid_p_tags, p_texts
        )
    else:
        figures, tables = [], []

    extract_time = time.time() - t_extract

    # --------------------------------------------------
    # [AGGIUNTO] STAMPA TEMPI (durante pipeline)
    # --------------------------------------------------
    print(
        f"[TIMING] {paper_id} | "
        f"HTML parsing: {parsing_time:.2f}s | "
        f"TF-IDF: {tfidf_time:.2f}s | "
        f"Multimedia extraction: {extract_time:.2f}s"
    )

    # --------------------------------------------------
    # [NOTA] NON cambiamo il return per compatibilità
    # --------------------------------------------------
    return figures, tables


# LOGICA SPECIFICA: ARXIV
def _extract_arxiv(soup, paper_id, analyzer, p_tags, p_texts):
    figures_data = []
    tables_data = []

    # Base URL
    base_url = ""
    base_tag = soup.find("base")
    if base_tag:
        href_val = _get_attr_str(base_tag, "href")
        if href_val:
            base_url = "https://arxiv.org" + href_val if href_val.startswith("/") else f"https://arxiv.org/{href_val}"

    # Estrazione FIGURE
    all_figures = soup.find_all("figure", class_="ltx_figure")
    
    for fig in all_figures:
        if "ltx_table" in _get_attr_str(fig, "class"):
            continue
            
        if fig.find_parent("figure", class_="ltx_figure"):
            continue

        parent_id = _get_attr_str(fig, "id") or "unknown"
        sub_figures = fig.find_all("figure", class_="ltx_figure")
        
        if sub_figures:
            direct_captions = [
                c for c in fig.find_all("figcaption") 
                if c.find_parent("figure", class_="ltx_figure") == fig
            ]
            main_caption_text = " ".join(
                [clean_text(c.get_text()) for c in direct_captions]
            )
            
            for sub in sub_figures:
                sub_id = _get_attr_str(sub, "id") or "unknown"
                sub_caps = sub.find_all("figcaption")
                sub_caption_text = " ".join(
                    [clean_text(c.get_text()) for c in sub_caps]
                )
                
                img_tag = sub.find("img")
                img_src = _get_attr_str(img_tag, "src") if img_tag else ""
                img_url = f"{base_url}{img_src}" if (img_src and base_url) else ""
                
                full_caption = f"{sub_caption_text} {main_caption_text}".strip()
                
                mentions, mention_idxs = _find_mentions(p_tags, p_texts, parent_id)
                if sub_id != parent_id:
                    m_sub, m_idxs_sub = _find_mentions(p_tags, p_texts, sub_id)
                    mentions.extend(m_sub)
                    mention_idxs.update(m_idxs_sub)
                
                context = analyzer.find_context(
                    full_caption, exclude_indices=mention_idxs
                )
                
                figures_data.append({
                    "source": "arxiv",
                    "paper_id": paper_id,
                    "figure_id": sub_id,
                    "img_url": img_url,
                    "local_src": img_src,
                    "caption": full_caption,
                    "mentions": list(set(mentions)),
                    "context_paragraphs": context
                })

    # Estrazione tabelle
    table_nodes = soup.find_all("figure", class_="ltx_table")
    for tbl in table_nodes:
        t_id = _get_attr_str(tbl, "id") or "unknown"
        caption_tag = tbl.find("figcaption")
        caption = clean_text(caption_tag.get_text()) if caption_tag else ""
        
        body_content = ""
        real_tbl = tbl.find("table")
        if real_tbl:
            body_content = clean_text(real_tbl.get_text(separator=" "))
            
        mentions, mention_idxs = _find_mentions(p_tags, p_texts, t_id)
        context = analyzer.find_context(
            caption + " " + body_content,
            exclude_indices=mention_idxs
        )

        if caption or body_content:
            tables_data.append({
                "source": "arxiv",
                "paper_id": paper_id,
                "table_id": t_id,
                "caption": caption,
                "body_content": body_content,
                "mentions": mentions,
                "context_paragraphs": context
            })

    return figures_data, tables_data


# LOGICA SPECIFICA: PUBMED
def _extract_pubmed(soup, paper_id, analyzer, p_tags, p_texts):
    figures_data = []
    tables_data = []

    real_paper_id = paper_id
    all_figures = soup.find_all("figure")
    
    for fig in all_figures:
        fig_class = _get_attr_str(fig, "class")
        if "table" in fig_class or fig.find("table"):
            continue

        f_id = _get_attr_str(fig, "id") or "unknown"
        caption_tag = fig.find("figcaption")
        raw_cap = clean_text(caption_tag.get_text()) if caption_tag else ""
        
        label_tag = fig.find(["h3", "h4", "strong"], class_="obj_head")
        label_text = clean_text(label_tag.get_text()) if label_tag else ""
        
        caption = (
            f"{label_text} {raw_cap}"
            if label_text and label_text not in raw_cap
            else raw_cap
        )

        img_url = ""
        img_src = ""
        img_tag = fig.find("img")
        if img_tag:
            img_src = _get_attr_str(img_tag, "src")
            if img_src:
                img_url = img_src if img_src.startswith("http") \
                    else f"https://pmc.ncbi.nlm.nih.gov{img_src}"

        if not img_url and not caption:
            continue

        mentions, mention_idxs = _find_mentions(p_tags, p_texts, f_id)
        context = analyzer.find_context(
            caption, exclude_indices=mention_idxs
        )

        figures_data.append({
            "source": "pubmed",
            "paper_id": real_paper_id,
            "figure_id": f_id,
            "img_url": img_url,
            "local_src": img_src,
            "caption": caption,
            "mentions": mentions,
            "context_paragraphs": context
        })

    # Estrazione tabelle
    table_nodes = soup.find_all(
        ["div", "section"],
        class_=lambda x: x and ("table-wrap" in x or "tw" in x)
    )
    
    for tbl in table_nodes:
        t_id = _get_attr_str(tbl, "id") or "unknown"
        label_tag = tbl.find(["h3", "h4", "strong"], class_="obj_head")
        label_text = clean_text(label_tag.get_text()) if label_tag else ""
        
        desc_tag = tbl.find(class_="caption")
        desc_text = clean_text(desc_tag.get_text()) if desc_tag else ""
        
        caption = (
            f"{label_text} {desc_text}"
            if label_text and label_text not in desc_text
            else desc_text
        )

        body_content = ""
        real_tbl = tbl.find("table")
        if real_tbl:
            body_content = clean_text(real_tbl.get_text(separator=" "))

        if not body_content and not caption:
            continue

        mentions, mention_idxs = _find_mentions(p_tags, p_texts, t_id)
        context = analyzer.find_context(
            caption + " " + body_content,
            exclude_indices=mention_idxs
        )

        tables_data.append({
            "source": "pubmed",
            "paper_id": real_paper_id,
            "table_id": t_id,
            "caption": caption,
            "body_content": body_content,
            "mentions": mentions,
            "context_paragraphs": context
        })

    return figures_data, tables_data
