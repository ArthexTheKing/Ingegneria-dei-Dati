# Homework 2
Questo progetto indicizza file `.txt` contenenti materiale sul Deep Learning e permette di eseguire ricerche full-text tramite console.

## ✅ Funzionalità
- Indicizzazione automatica file `.txt`
- Campi indicizzati:
  - filename (keyword + lowercase normalizer)
  - content (text, english analyzer)
- Supporto phrase query con virgolette
- Ricerca interattiva da console

## 🛠️ Tecnologie
- Python: 3.14+
- Elasticsearch: 9.2.0

### Installare dipendenze
Librerie Python necessarie per l'esecuzione del progetto
```bash
pip install -r requirements.txt
```