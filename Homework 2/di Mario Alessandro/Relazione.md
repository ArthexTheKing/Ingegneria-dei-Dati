# 📄 Relazione Homework 2: Indicizzazione e Ricerca Documenti TXT (Deep Learning)

## 🛠️ Architettura del Sistema
Il sistema è stato realizzato in **Python** utilizzando la libreria `elasticsearch` per l'interazione con il motore di ricerca. L'indicizzazione avviene su file `.txt` contenuti nella directory locale `documenti_deep_learning`. Sono stati creati due indici/campi per ciascun documento: il **nome del file** e il **contenuto del file**.

### 1. Analizzatori Scelti (e Motivazione)

Gli analizzatori sono stati configurati a livello di mapping di Elasticsearch.

| Campo | Analizzatore | Tokenizer e Filtri | Motivazione della Scelta |
| :--- | :--- | :--- | :--- |
| **`nome`** | `filename_analyzer` (Personalizzato) | **`whitespace`**, `lowercase`, `italian_stop` | Il tokenizer **`whitespace`** è stato scelto per la sua semplicità e robustezza. Per garantire il corretto funzionamento delle query sul nome, i nomi dei file sono stati modificati per utilizzare lo **spazio** come unico delimitatore tra le parole (es. `introduzione reti neurali.txt`). |
| **`contenuto`** | **`italian`** (Standard) | `standard`, `lowercase`, `stop` (`italian`), `stemmer` (`italian`) | **Scelta ottimale per i testi in italiano.** Questo analizzatore standard include lo **stemming**, che riduce le parole alla loro radice (es: "applicazioni" $\rightarrow$ "applic"), migliorando il *recall* della ricerca sul contenuto. |

---

### 2. Dati di Indicizzazione e Prestazioni

I file indicizzati sono 10, con contenuto corposo sul Deep Learning. Il tempo di indicizzazione è stato misurato utilizzando il modulo `time` di Python.

* **Numero di file indicizzati:** **10**
* **Tempo totale di indicizzazione:** **0.5321** secondi

---

### 3. Query di Test Utilizzate

Il programma di interrogazione accetta query con la sintassi `campo:termine` o `campo:"phrase query"`. Le 10 query di test coprono scenari di ricerca per nome, contenuto, booleane e phrase query.

| \# | Query | Campo Interrogato | Tipo di Ricerca | Obiettivo del Test |
| :--- | :--- | :--- | :--- | :--- |
| **1** | `nome:backpropagation` | `nome` | Termine Singolo | Verifica la ricerca per nome del file. |
| **2** | `nome:"reti neurali"` | `nome` | Phrase Query | Testare la ricerca di una frase esatta nel nome. |
| **3** | `contenuto:classificazione` | `contenuto` | Termine Singolo | Testare l'efficacia dello **stemming** (trova termini come "classificazione" anche se la query è al singolare). |
| **4** | `contenuto:"dati sequenziali"` | `contenuto` | Phrase Query | Verificare la ricerca di una sequenza esatta di parole nel contenuto esteso. |
| **5** | `contenuto:imaging OR contenuto:raggi` | `contenuto` | Booleana OR | Verifica la ricerca di uno dei due concetti medici nel contenuto. |
| **6** | `contenuto:sfide AND contenuto:black` | `contenuto` | Booleana AND | Verificare l'AND implicito tra concetti chiave ("sfide" e "black box") nello stesso documento. |
| **7** | `nome:tensorflow OR nome:pytorch` | `nome` | Booleana OR | Testare la ricerca disgiuntiva sui titoli dei file. |
| **8** | `nome:"reti generative" AND contenuto:generatore` | `nome` e `contenuto` | Ricerca Mista | Combinare la ricerca su entrambi gli indici. |
| **9** | `contenuto:sequenze OR nome:trasformatore` | `contenuto` e `nome` | Ricerca Mista OR | Ricerca alternativa tra un concetto nel contenuto e una parola nel titolo. |
| **10** | `nome:apprendimento*` | `nome` | Wildcard | Testare la ricerca con caratteri jolly (`*`) sul nome del file. |