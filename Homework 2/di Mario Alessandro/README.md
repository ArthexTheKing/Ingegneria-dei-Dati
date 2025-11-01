# Sistema di indicizzazione file `.txt` in italiano con Elasticsearch

## 1. Obiettivo
Realizzare un sistema che indicizza file `.txt` in lingua italiana e permette di eseguire ricerche full-text tramite console usando Elasticsearch.

Campi indicizzati:
- nome del file
- contenuto del file

Tema dei file: **Deep Learning / Apprendimento automatico**

---

## 2. Scelte sugli Analyzer

| Campo | Analyzer | Motivazione |
|---|---|---|
`file_name` | `simple` | I nomi file non richiedono stopwords; utile per tokenizzare parole composte |
`content` | `standard + stopwords italiane` | Migliora la ricerca eliminando articoli e preposizioni in italiano |

---

## 3. Dati indicizzati

| Parametro | Valore |
|---|---|
File | 10 `.txt` in italiano  
Dimensione media file | 1–2 KB  
Tempo di indicizzazione | ~0.31 secondi  

---

## 4. Query di test

| Query | Scopo |
|---|---|
`nome:convoluzionali` | Ricerca file da nome parziale
`nome:backpropagation` | Ricerca file con termine tecnico 
`nome:reti` | Ricerca con parti di nomi identiche
`nome:"transfer learning"` | Ricerca di uno specifico documento
`nome:introduzione` | Ricerca di uno specifico documento di un singolo termine
`contenuto:apprendimento` | Ricerca di un termine generico relativo all'argomento 
`contenuto:"apprendimento profondo"` | frase completa  
`contenuto:"rete neurale"` | match di una frase completa
`contenuto:backpropagation` | Ricerca di un termine tecnico
`contenuto:"computer vision"` | Ricerca di una frase tecnica 

---

## 5. Conclusioni
Il sistema consente l'indicizzazione e la ricerca efficace di testi tecnici in italiano sul deep learning tramite Elasticsearch, utilizzando analyzer adeguati alla lingua e supportando phrase query.
