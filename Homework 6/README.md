# Pipeline di Integrazione Dati Automotive

**Corso:** Ingegneria dei Dati 2025/2026  
**Argomento:** Entity Resolution e Data Integration su Dataset Automotive Eterogenei

## Panoramica del Progetto

Questo progetto implementa una pipeline di integrazione dati end-to-end progettata per allineare record di veicoli provenienti da due sorgenti distinte: *Craigslist* (caratterizzato da contenuti generati dagli utenti, non strutturati e rumorosi) e *US Used Cars* (dati strutturati).

L'obiettivo primario è valutare e confrontare tre distinte metodologie di Entity Resolution (ER):
1.  **Record Linkage Basato su Regole:** Un approccio deterministico che utilizza regole manuali e metriche di similarità (Jaro-Winkler).
2.  **Active Learning (Dedupe):** Un approccio di machine learning che apprende iterativamente i pesi delle feature attraverso l'etichettatura human-in-the-loop.
3.  **Deep Learning (Ditto):** Un modello di entity matching allo stato dell'arte basato su Transformer pre-addestrati (DistilBERT), eseguito su Google Colab.

## Struttura della Repository

La repository è organizzata come segue:

* `data/`: Directory contenente i dataset elaborati generati dagli script della pipeline.
* `MainCampionato.py`: Script di esecuzione principale per il dataset campionato (circa 2000 coppie), ottimizzato per test rapidi e debugging.
* `MainNonCampionato.py`: Script di esecuzione principale per l'intersezione completa del dataset (circa 4000 coppie), utilizzato per la validazione finale.
* `ditto.ipynb`: Jupyter Notebook configurato per Google Colab, contenente la pipeline completa di Deep Learning (setup, training, inferenza).
* `requirements.txt`: Lista delle dipendenze Python richieste per l'esecuzione locale.
* `Relazione HomeWork6.pdf`: Relazione tecnica che dettaglia la metodologia, le sfide affrontate e i risultati sperimentali.

## Metodologia

### 1. Mediazione dello Schema e Pre-elaborazione
Gli attributi di entrambe le sorgenti sono stati mappati su uno schema mediato globale che include campi come `vin`, `make`, `model`, `year`, `price`, `mileage` e `description`. La pulizia dei dati ha comportato la normalizzazione dei campi testuali e la standardizzazione dei valori numerici.

### 2. Generazione della Ground Truth e Prevenzione del Data Leakage
Una Ground Truth affidabile è stata stabilita utilizzando il Vehicle Identification Number (VIN) come chiave univoca. Per garantire uno scenario di valutazione realistico e prevenire il data leakage, l'attributo VIN è stato rigorosamente rimosso dai set di training, validazione e test. Questo forza i modelli ad apprendere le corrispondenze basandosi esclusivamente sugli attributi descrittivi.

### 3. Strategie di Blocking
Per affrontare la complessità computazionale dei prodotti cartesiani, sono state implementate due strategie di blocking:
* **B1 (Blocking Standard):** Blocking esatto sull'attributo `make`.
* **B2 (Sorted Neighborhood):** Approccio a finestra mobile sull'attributo `year` (dimensione finestra = 1).

## Istruzioni per l'Esecuzione

### Esecuzione Locale (Pre-elaborazione & Baseline)
Gli script Python locali gestiscono la preparazione dei dati, la generazione della Ground Truth e l'esecuzione delle baseline di Record Linkage e Dedupe.

1.  Installare le dipendenze richieste:
    ```bash
    pip install -r requirements.txt
    ```
2.  Posizionare i file dei dataset grezzi (`vehicles.csv` e `used_cars_data.csv`) nella directory `data/dataset/`.
3.  Eseguire lo script della pipeline desiderato:
    ```bash
    python MainCampionato.py
    # OPPURE
    python MainNonCampionato.py
    ```
    *Output:* Questi script generano i file dataset serializzati (`ditto_train.txt`, `ditto_val.txt`, `ditto_test.txt`) richiesti per la fase di Deep Learning.

### Esecuzione Deep Learning (Google Colab)
Il modello Ditto richiede accelerazione GPU. Il notebook fornito è ottimizzato per l'ambiente Google Colab.

1.  Caricare `ditto.ipynb` su Google Colab.
2.  Caricare i file `.txt` generati nel passaggio precedente nella sessione Colab.
3.  Eseguire le celle del notebook. Lo script include patch automatizzate per risolvere specifici problemi di compatibilità con la repository `FAIR-DA4ER/ditto`:
    * Correzione del parsing della separazione a tabulazioni in `dataset.py`.
    * Fix per il caricamento del `state_dict` in `matcher.py`.
    * Regolazione del batch size (ridotto a 16) per prevenire errori CUDA Out Of Memory.

## Risultati Sperimentali

La valutazione è stata condotta su un test set separato. L'approccio di Deep Learning (Ditto) ha dimostrato prestazioni superiori nella gestione di dati rumorosi e non strutturati rispetto ai metodi tradizionali.

| Pipeline | Precision | Recall | F1-Score | Tempo di Inferenza |
| :--- | :---: | :---: | :---: | :---: |
| **Record Linkage (B1)** | 0.04 | 0.94 | 0.07 | ~9.2s |
| **Dedupe (B1)** | 0.12 | 0.57 | 0.20 | ~134s |
| **Ditto (Deep Learning)** | **0.97** | **0.88** | **0.92** | ~94s |

*Nota: I risultati corrispondono all'esperimento sul dataset campionato eseguito su Google Colab.*