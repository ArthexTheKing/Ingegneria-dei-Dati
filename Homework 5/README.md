# Scientific Corpus Search Engine

Questo progetto è un motore di ricerca semantico modulare progettato per recuperare, analizzare e indicizzare letteratura scientifica proveniente da ArXiv e PubMed Central (PMC).

Il sistema indicizza il testo completo dei documenti ed estrae separatamente tabelle e figure, arricchendole con il contesto semantico (paragrafi rilevanti) calcolato tramite algoritmi TF-IDF e Cosine Similarity.

## Funzionalità Principali

* **Ingestion Multi-Sorgente:** Scarica automaticamente metadati e contenuti completi da ArXiv (via API e HTML) e PubMed Central.
* **Strategia Ibrida PubMed:** Utilizza file XML per l'estrazione accurata dei metadati e parsing HTML per i contenuti multimediali.
* **Estrazione Multimediale:** Parsing avanzato dell'HTML per separare figure e tabelle dal testo principale.
* **Analisi Semantica del Contesto:** Utilizza `TfidfVectorizer` per associare a ogni figura o tabella i paragrafi del testo che la descrivono o citano.
* **Backend Elasticsearch:** Indicizzazione su tre indici separati: Documenti, Tabelle e Figure.
* **Doppia Interfaccia:**
  * **CLI Shell:** Interfaccia a riga di comando per query rapide.
  * **Web App:** Interfaccia web basata su Flask con evidenziazione dei risultati (highlighting) e anteprima immagini.

## Struttura del Progetto

search_engine_project/
├── data/                   # Cartella di output (generata a runtime)
├── src/
│   ├── config.py           # Configurazione centralizzata
│   ├── core/               # Gestione Elasticsearch e utility
│   ├── ingestion/          # Moduli download (ArXiv/PubMed)
│   ├── processing/         # Estrattore HTML e Analisi Semantica
│   └── web/                # Applicazione Flask e template
├── run_pipeline.py         # Script di indicizzazione (ETL)
├── run_shell.py            # Interfaccia CLI
├── run_web.py              # Server Web
├── docker-compose.yml      # Configurazione Elasticsearch
├── requirements.txt        # Dipendenze Python
└── README.md               # Documentazione

## Prerequisiti

* Python 3.9 o superiore
* Docker e Docker Compose (per eseguire Elasticsearch)
* Connessione internet attiva

## Installazione

1. **Clonare il repository:**
   git clone <url-tua-repo>
   cd search_engine_project

2. **Creare un ambiente virtuale (consigliato):**
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # oppure
   venv\Scripts\activate     # Windows

3. **Installare le dipendenze:**
   pip install -r requirements.txt

4. **Avviare Elasticsearch:**
   Il progetto include un file `docker-compose.yml` preconfigurato (versione 9.2.0, senza sicurezza per sviluppo locale).
   
   docker-compose up -d

   Verificare che sia attivo su: http://localhost:9200

## Configurazione Ambiente (.env)

**IMPORTANTE:** Questo progetto richiede variabili d'ambiente per funzionare correttamente. Poiché contengono informazioni sensibili o configurazioni locali, il file `.env` **NON è incluso nel repository**.

È necessario creare manualmente un file chiamato `.env` nella radice del progetto e inserire il seguente contenuto:

```env
# Configurazione Elasticsearch
ES_HOST=http://localhost:9200

# Configurazione PubMed (Obbligatoria per le API NCBI)
# Inserire un indirizzo email valido per evitare blocchi IP da parte di NCBI
PUBMED_EMAIL=tua_email@example.com