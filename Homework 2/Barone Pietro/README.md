# Data Engineering Projects

## HW2 – Text Indexing with Lucene

### Project Structure and Execution

#### General Architecture

The project was developed in **Java**, using the **Apache Lucene** library for text indexing and search.

The main files in the project are:

* **`Indexer.java`**  
  Responsible for indexing all `.txt` files located in the `text/` directory.  
  Uses a **StandardAnalyzer** for the `content` field and a **StringField** for the `name` field, in order to build a searchable text index.  
  The index is stored inside the `index/` folder and is overwritten each time the indexer is executed.

* **`Searcher.java`**  
  Handles search operations over the created index.  
  Supports both single-term queries (e.g., `content:lucene`) and phrase queries (e.g., `content:"search engines"`), simulating the behavior of the **StandardAnalyzer** even for *PhraseQuery* processing.  
  Additionally, it allows **exact lookups** on the file name (`name` field) using a **TermQuery**.

* **`ConfigLoader.java`**  
  Utility class that loads configuration parameters defined in `config.properties`.  
  The configuration file specifies paths such as `index.path` and `text.path`, ensuring that no hard-coded paths are required in the source code.

* **`MainApp.java`**  
  Acts as an **orchestrator** and provides an **interactive terminal menu**, allowing the user to choose whether to execute indexing or search operations.

---

### Project Execution Methods

The project can be executed in two alternative ways:
* **Maven**
* **`javac`** and **`java`** commands.

---

#### Execution via Maven

Requirements:

* **JDK 17** or later  
* **Apache Maven 3.8+**

Commands to run from the project root:

```bash
mvn clean compile                              # Compile the source code
mvn exec:java -Dexec.mainClass="it.uniroma3.MainApp"   # Run the main program
````

---

#### Manual Execution with `javac` and `java`

If Maven is not used, the project can be executed manually by:

* Installing **JDK 17** or higher
* Downloading the required **Lucene libraries** manually, for example:
  `lucene-core-9.2.0.jar`, `lucene-analyzers-common-9.2.0.jar`,
  `lucene-queryparser-9.2.0.jar`, `lucene-codecs-9.2.0.jar`
* Placing all `.jar` files inside the `lib/` folder

Commands to execute from the project root:

```bash
javac -cp "lib/*" -d .class src/main/java/it/uniroma3/*.java   # Compilation
java -cp ".class;lib/*" it.uniroma3.MainApp                     # Run (Windows)
```

Alternatively, to run modules individually:

```bash
java -cp ".class;lib/*" it.uniroma3.Indexer   # Indexing (Windows)
java -cp ".class;lib/*" it.uniroma3.Searcher  # Searching (Windows)
```

> **Note:** On **Linux** or **macOS**, replace the semicolon `;` with a colon `:` in the classpath:
>
> ```bash
> java -cp ".class:lib/*" it.uniroma3.MainApp
> ```


## HW1 – Text Indexing with Elasticsearch

The project aims to index and search text documents using **Elasticsearch**.

The main files in the project are:

* **indexer.py**: indexes all .txt files in the `text/` folder, applying the Italian analyzer to the content. It also analyzes the field tokens and saves the results in a JSON file, including the total indexing time.
* **searcher.py**: allows interactive searches on the index, supporting term, match, and match phrase queries.
* **mainApp.py**: main application that allows you to interactively choose whether to index files or perform searches, calling the functions of indexer.py and searcher.py.
* **config.py**: contains all configurations, such as the Elasticsearch URL, index name, text file folder, and settings for previewing content in searches.
* **indexerBenchmark.py**: experimental script used to compare the performance of bulk indexing and single indexing, measuring the average (median) time over multiple runs.

### Project implementation methods

The search engine can be easily run by complying with the requirements and executing the commands provided.

**Requirements:**

* Python 3.10+
* Elasticsearch running on `http://localhost:9200`
* Python libraries `elasticsearch`, `datasets` e `pandas`

**Commands to be executed in the main project folder:**

```bash
# Execution
python .\mainApp.py
```

Alternatively, to run the modules individually:

```bash
# Indexing and search
python .\indexer.py
python .\indexerBenchmark.py
python .\searcher.py
```

---