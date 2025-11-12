package it.uniroma3;

import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.document.Document;
import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.index.StoredFields;
import org.apache.lucene.index.Term;
import org.apache.lucene.store.FSDirectory;
import org.apache.lucene.queryparser.classic.QueryParser;
import org.apache.lucene.search.*;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.file.Paths;
import java.util.Properties;

public class Searcher {
    public static void main(String[] args) throws Exception {
        
        // Load configuration properties
        Properties configProperties = ConfigLoader.loadConfig();
        String INDEX_PATH = configProperties.getProperty("index.path", "index");
        int NUMBER_OF_RESULTS = Integer.parseInt(configProperties.getProperty("number.of.results", "10"));

        System.out.println("\nInsert query (es. nome:termQuery or contenuto:query or contenuto:\"phraseQuery\")\nType exit to quit\n");

        try (FSDirectory dir = FSDirectory.open(Paths.get(INDEX_PATH)); DirectoryReader reader = DirectoryReader.open(dir); Analyzer analyzer = new StandardAnalyzer();) {

            IndexSearcher searcher = new IndexSearcher(reader);
            BufferedReader in = new BufferedReader(new InputStreamReader(System.in));

            while (true) {
                System.out.print("> ");
                String line = in.readLine();

                // If input is null or user types "exit", stop the loop
                if (line == null || line.trim().equalsIgnoreCase("exit")) {
                    System.out.println("exiting...\n");
                    break;
                }

                // Split input into two parts divided by the first ":"
                String[] parts = line.split(":", 2);

                // If there are not exactly 2 parts, syntax error
                if (parts.length != 2) {
                    System.out.println("Syntax error! Use nome:termQuery or contenuto:query or contenuto:\"phraseQuery\"\n");
                    continue;
                }

                // Remove leading and trailing whitespace
                String field = parts[0].strip();
                String queryStr = parts[1].strip();

                Query query;

                if (field.equals("nome")) {
                    query = new TermQuery(new Term("nome", queryStr));
                    System.out.println("Searching for: " + "\"" + queryStr + "\" in field: " + "\"" + field + "\"\n");
                } else {
                    boolean isPhrase = queryStr.startsWith("\"") && queryStr.endsWith("\"");

                    if (isPhrase) {
                        // Remove surrounding quotes
                        String phrase = queryStr.substring(1, queryStr.length() - 1);

                        // Simulate StandardAnalyzer (lowercase, no stopwords)
                        String[] tokens = phrase
                            .toLowerCase()
                            .replaceAll("[^\\p{L}\\p{N}\\s]", "")
                            .split("\\s+");

                        PhraseQuery.Builder phraseBuilder = new PhraseQuery.Builder();
                        int pos = 0;
                        for (String token : tokens) {
                            if (!token.isBlank()) {
                                phraseBuilder.add(new Term(field, token), pos++);
                            }
                        }
                        query = phraseBuilder.build();
                    
                    } else {
                        // Standard text query
                        QueryParser parser = new QueryParser(field, analyzer);
                        query = parser.parse(queryStr);
                    }
                }               

                // Search top results
                TopDocs hits = searcher.search(query, NUMBER_OF_RESULTS);
                StoredFields storedFields = searcher.storedFields();

                // Iterate through hits and print results
                for (int i = 0; i < hits.scoreDocs.length; i++) { 
                    ScoreDoc scoreDoc = hits.scoreDocs[i]; 
                    Document doc = storedFields.document(scoreDoc.doc);
                    String titolo = doc.get("nome");
                    String contenuto = doc.get("contenuto");
                    System.out.println(i+1+"° hit: "+titolo +"\n"+contenuto+"\n");
                }
            }
        }
    }
}