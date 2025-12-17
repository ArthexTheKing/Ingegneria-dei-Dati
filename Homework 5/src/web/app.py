from flask import Flask, render_template, request
from src.core import get_es_client
from src.config import Config

app = Flask(__name__)

# Mappatura tra Indici Elasticsearch e "Tipi" visuali del Template HTML
INDEX_TYPE_MAP = {
    Config.INDEX_DOCS: "docs",
    Config.INDEX_TABLES: "tables",
    Config.INDEX_FIGURES: "figures"
}

def get_highlighted_snippet(hit, field_name, fallback_text="", length=300):
    """
    Estrae il testo evidenziato da ES. Se non c'è match, usa il testo originale troncato.
    """
    highlight = hit.get("highlight", {})
    if field_name in highlight:
        return "... " + " ... ".join(highlight[field_name]) + " ..."
    
    if not fallback_text:
        return ""
    
    text_str = str(fallback_text)
    if len(text_str) > length:
        return text_str[:length] + "..."
    return text_str

@app.route("/", methods=["GET", "POST"])
def search():
    results = []
    query = ""
    selected_mode = "all"
    total_hits = 0

    if request.method == "POST":
        query = request.form.get("query", "").strip()
        selected_mode = request.form.get("mode", "all")
        
        if query:
            try:
                es = get_es_client()
                
                indices_to_search = []
                if selected_mode == "docs": indices_to_search = [Config.INDEX_DOCS]
                elif selected_mode == "tables": indices_to_search = [Config.INDEX_TABLES]
                elif selected_mode == "figures": indices_to_search = [Config.INDEX_FIGURES]
                else: indices_to_search = [Config.INDEX_DOCS, Config.INDEX_TABLES, Config.INDEX_FIGURES]

                for idx in indices_to_search:
                    visual_type = INDEX_TYPE_MAP.get(idx, "docs")

                    # Campi di ricerca specifici
                    search_fields = ["*"]
                    if visual_type == "docs":
                        search_fields = ["title^3", "abstract^2", "full_text", "authors", "document_id"]
                    elif visual_type == "tables":
                        search_fields = ["caption^3", "body_content^2", "mentions", "context_paragraphs", "table_id"]
                    elif visual_type == "figures":
                        search_fields = ["caption^3", "mentions", "context_paragraphs", "figure_id"]

                    body = {
                        "query": {
                            "query_string": {
                                "query": query,
                                "fields": search_fields,
                                "default_operator": "AND"
                            }
                        },
                        "highlight": {
                            "fields": { "*": {} },
                            "pre_tags": ["<mark>"],
                            "post_tags": ["</mark>"],
                            "fragment_size": 200,
                            "number_of_fragments": 1
                        },
                        "size": 10
                    }
                    
                    resp = es.search(index=idx, body=body)
                    hits = resp['hits']['hits']
                    
                    for hit in hits:
                        src = hit['_source']
                        
                        # --- LOGICA TITOLO MIGLIORATA ---
                        title_val = "Senza Titolo"
                        
                        if visual_type == "docs":
                            # Documenti: Titolo Paper > Nome File > Fallback
                            title_val = src.get("title") or src.get("paper_title_slug") or "Documento sconosciuto"
                        else:
                            # Media: Caption troncata > ID Figura > Fallback
                            caption_raw = src.get("caption", "")
                            if caption_raw:
                                # Usa i primi 100 caratteri della caption come titolo "pulito"
                                clean_cap = str(caption_raw).strip()
                                title_val = clean_cap[:100] + ("..." if len(clean_cap) > 100 else "")
                            else:
                                # Fallback su ID (es. "Figure 1", "Table S2")
                                obj_id = src.get("figure_id") or src.get("table_id")
                                title_val = f"Oggetto: {obj_id}" if obj_id else "Immagine senza descrizione"

                        # Snippet Primario (Abstract o Caption evidenziata)
                        if visual_type == "docs":
                            prim_text = get_highlighted_snippet(hit, "abstract", src.get("abstract"))
                        else:
                            prim_text = get_highlighted_snippet(hit, "caption", src.get("caption"))
                        
                        # Snippet Secondario (Contesto o Full Text)
                        sec_text = ""
                        if visual_type == "docs":
                            if "full_text" in hit.get("highlight", {}):
                                sec_text = get_highlighted_snippet(hit, "full_text")
                        else:
                            sec_text = get_highlighted_snippet(hit, "context_paragraphs", src.get("context_paragraphs"))
                            if not sec_text:
                                sec_text = get_highlighted_snippet(hit, "mentions", src.get("mentions"))

                        res_item = {
                            "type": visual_type,
                            "score": hit['_score'],
                            "paper_id": src.get("document_id") or src.get("paper_id"),
                            "title_or_slug": title_val, # Qui ora c'è la caption troncata!
                            "url": src.get("pdf_url") or src.get("img_url"),
                            "primary_text": prim_text,
                            "secondary_text": sec_text,
                            "source_data": src
                        }
                        results.append(res_item)

                results.sort(key=lambda x: x['score'], reverse=True)
                total_hits = len(results)

            except Exception as e:
                print(f"Errore Search Web: {e}")

    return render_template(
        "search.html", 
        results=results, 
        query=query, 
        selected_mode=selected_mode,
        total_hits=total_hits
    )