# Scientific Corpus Search Engine

Questo progetto è un motore di ricerca semantico modulare progettato per recuperare, analizzare e indicizzare letteratura scientifica proveniente da ArXiv e PubMed Central (PMC).

Il sistema indicizza il testo completo dei documenti ed estrae tabelle e figure come entità di ricerca indipendenti, arricchendole con il contesto semantico (paragrafi rilevanti) calcolato tramite algoritmi TF-IDF e Cosine Similarity.

## Funzionalità Principali

* **Ingestion Multi-Sorgente:** Scarica automaticamente metadati e contenuti completi da ArXiv (via API e HTML) e PubMed Central.
* **Strategia Ibrida PubMed:** Utilizza file XML per l'estrazione accurata dei metadati (titolo, autori, abstract, data) e parsing HTML per i contenuti multimediali.
* **Estrazione Multimediale:** Parsing avanzato dell'HTML per separare figure e tabelle dal testo principale.
* **Analisi Semantica del Contesto:** Utilizza TfidfVectorizer per associare a ogni figura o tabella i paragrafi del testo che la descrivono, migliorando la precisione della ricerca.
* **Backend Elasticsearch:** Indicizzazione su tre indici separati: Documenti, Tabelle e Figure.
* **Doppia Interfaccia:**
  * **CLI Shell:** Interfaccia a riga di comando per test e query rapide.
  * **Web App:** Interfaccia web basata su Flask con evidenziazione dei risultati (highlighting).

## Struttura del Progetto

Il progetto segue un'architettura modulare:

search_engine_project/
├── data/                   # Cartella di output per i file scaricati (generata a runtime)
├── src/
│   ├── config.py           # Configurazione centralizzata (query, percorsi, costanti)
│   ├── core/               # Gestione connessione Elasticsearch e utility
│   ├── ingestion/          # Moduli di download (ArXiv e PubMed)
│   ├── processing/         # Logica di estrazione HTML e analisi TF-IDF
│   └── web/                # Applicazione Flask
├── run_pipeline.py         # Script per scaricare, processare e indicizzare i dati
├── run_shell.py            # Interfaccia di ricerca a riga di comando (CLI)
├── run_web.py              # Server web per l'interfaccia grafica
├── requirements.txt        # Dipendenze Python
└── README.md               # Documentazione

## Prerequisiti

* Python 3.9 o superiore
* Elasticsearch 8.x (in esecuzione locale o remota)
* Connessione internet attiva

## Installazione

1. Clonare il repository o scaricare i file del progetto.

2. Creare un ambiente virtuale (opzionale ma consigliato):
   python -m venv venv
   source venv/bin/activate  # Su Linux/Mac
   # oppure
   venv\Scripts\activate     # Su Windows

3. Installare le dipendenze:
   pip install -r requirements.txt

4. Configurare Elasticsearch:
   Assicurarsi che Elasticsearch sia attivo. Il progetto punta di default a http://localhost:9200.
   È possibile modificare questo parametro nel file src/config.py o tramite variabile d'ambiente ES_HOST.

## Utilizzo

### 1. Indicizzazione (Pipeline)

Per scaricare gli articoli e popolare il database:

python run_pipeline.py

Questo script esegue:
- Reset degli indici Elasticsearch.
- Download metadati e HTML da ArXiv e PubMed.
- Estrazione di testo, figure e tabelle.
- Calcolo del contesto semantico.
- Indicizzazione dei dati.

### 2. Ricerca CLI (Shell)

Per cercare direttamente dal terminale:

python run_shell.py

Seguire le istruzioni a schermo per selezionare l'indice desiderato (Documenti, Tabelle, Figure o Tutto).

### 3. Ricerca Web

Per avviare l'interfaccia grafica:

python run_web.py

Aprire il browser all'indirizzo http://localhost:5000.

## Configurazione

Le impostazioni principali sono in src/config.py:

* QUERY_ARXIV / QUERY_PUBMED: Stringhe di ricerca per il download.
* MAX_DOCS: Numero massimo di documenti da scaricare per fonte.
* TFIDF_THRESHOLD: Soglia di similarità (0.0 - 1.0) per il contesto semantico.
* PUBMED_EMAIL: Richiesta dalle API di NCBI per identificare l'utente.

## Note Tecniche

- Gestione Errori XML: Il modulo di ingestion PubMed include funzioni helper (_safe_get_text, _safe_get_int) per gestire la mancanza di nodi o attributi nei file XML forniti da eutils.
- Parsing Sicuro: L'estrattore HTML utilizza funzioni custom per gestire attributi ambigui di BeautifulSoup, prevenendo errori di tipo a runtime.