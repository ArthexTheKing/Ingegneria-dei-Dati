import os

# Definisce il percorso assoluto della directory dei documenti
# DOCS_DIR sarà: percorso_dello_script/documenti_deep_learning
DOCS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "documenti_deep_learning")

# Contenuti estesi per i documenti - NOMI FILE MODIFICATI CON SPAZIO
files_data_extended = [
    ("introduzione reti neurali.txt", "Una rete neurale è il blocco fondamentale del deep learning. È composta da strati di neuroni interconnessi: input, uno o più hidden layer e l'output. Ogni connessione ha un peso e ogni neurone ha un bias. Funzioni di attivazione come ReLU e Sigmoid introducono la non linearità. Il compito più comune è la classificazione di pattern."),
    ("apprendimento supervisionato e non.txt", "L'apprendimento supervisionato richiede un vasto set di dati etichettati, dove il modello impara a mappare gli input agli output corretti (come in regressione o classificazione). Al contrario, l'apprendimento non supervisionato lavora su dati senza etichette, focalizzandosi sulla scoperta di pattern nascosti, la riduzione della dimensionalità e il clustering. Molte sfide pratiche esistono in entrambi i campi, in particolare trovare dati di alta qualità."),
    ("cnn reti neurali convoluzionali.txt", "Le CNN (Convolutional Neural Networks) sono l'architettura dominante per l'analisi di immagini e dati spaziali. Utilizzano strati convoluzionali per applicare filtri e strati di pooling per ridurre la dimensione spaziale, mantenendo le feature importanti. Gli strati finali sono tipicamente fully-connected per la fase di predizione. Questo approccio ha rivoluzionato l'imaging e la visione artificiale."),
    ("rnn reti neurali ricorrenti.txt", "Le RNN (Recurrent Neural Networks) sono progettate per elaborare dati sequenziali come il testo o serie temporali. Hanno la capacità di mantenere uno 'stato' interno che rappresenta le informazioni passate. Tuttavia, soffrono del problema del vanishing gradient che impedisce di apprendere dipendenze a lungo termine. Per questo, le LSTM (Long Short-Term Memory) sono state introdotte come miglioramento, offrendo un meccanismo di gate per controllare il flusso di informazioni."),
    ("backpropagation come funziona.txt", "La backpropagation (retropropagazione dell'errore) è l'algoritmo chiave per addestrare le reti neurali. Dopo un forward pass che calcola l'output e la funzione di costo, il backward pass calcola il gradiente della funzione di costo rispetto ai pesi della rete. Questo gradiente indica la direzione e la magnitudine dell'errore e viene utilizzato da ottimizzatori (come l'Adam) per aggiornare i pesi e minimizzare l'errore."),
    ("tensorflow vs pytorch.txt", "TensorFlow e PyTorch sono i principali framework di deep learning. Storicamente, TensorFlow si basava su un grafo computazionale statico, offrendo vantaggi in produzione, mentre PyTorch usava un grafo dinamico, preferito per la ricerca e il debugging. Oggi, entrambi supportano grafi dinamici (eager execution). La scelta spesso dipende dall'ecosistema, dalla community e dalla specifica applicazione che si vuole sviluppare."),
    ("cos e un modello trasformatore.txt", "Il modello trasformatore, introdotto nel 2017, è l'architettura dominante in elaborazione del linguaggio naturale (NLP). A differenza delle RNN, esso si basa interamente sul meccanismo di attenzione (attention mechanism) per pesare l'importanza delle diverse parole nella sequenza di input. È composto da blocchi di encoder e decoder ed è alla base di modelli di grandi dimensioni come BERT e GPT. La sua capacità di parallelizzazione lo rende estremamente veloce."),
    ("applicazione deep learning medicina.txt", "Il deep learning è cruciale nella medicina per l'automazione di compiti complessi come la diagnosi di malattie. Esempi includono l'analisi di raggi X (radiologia), risonanze magnetiche e immagini istologiche. La sfida principale è ottenere grandi dataset medici etichettati in modo affidabile, ma i modelli stanno raggiungendo o superando la performance umana in compiti specifici."),
    ("sfide e limiti del deep learning.txt", "Le sfide riguardano principalmente l'interpretabilità (il problema della 'black box'), cioè la difficoltà di comprendere perché il modello ha preso una certa decisione. Inoltre, l'addestramento richiede quantità voluminose di dati etichettati e una potenza computazionale notevole. Il bias nei dati può anche portare a decisioni ingiuste o errate in contesti critici."),
    ("reti generative avversarie gan.txt", "Le GAN (Generative Adversarial Networks) sono una classe di reti neurali in cui due modelli, il Generatore e il Discriminatore, competono in un gioco a somma zero. Il Generatore crea nuovi dati (es. immagini false), mentre il Discriminatore cerca di distinguere i dati reali da quelli generati. Questo processo iterativo porta alla creazione di dati estremamente realistici, con applicazioni in sintesi di immagini e aumento di dataset.")
]

def generate_documents():
    """Crea la directory e i 10 file di testo nel percorso definito da DOCS_DIR."""
    if not os.path.isdir(DOCS_DIR):
        os.makedirs(DOCS_DIR)
        print(f"Directory '{DOCS_DIR}' creata.")
    
    print("Generazione dei file con contenuto esteso e spazi nei nomi...")
    for filename, content in files_data_extended:
        filepath = os.path.join(DOCS_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            
    print(f"Generazione completata. {len(files_data_extended)} file creati in '{DOCS_DIR}'.")

if __name__ == "__main__":
    generate_documents()