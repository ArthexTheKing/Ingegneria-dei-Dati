package it.uniroma3;

import org.apache.lucene.codecs.simpletext.SimpleTextCodec;
import org.apache.lucene.document.*;
import org.apache.lucene.index.*;
import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.FSDirectory;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Properties;
import java.util.stream.Stream;

public class Indexer {

    public static void main(String[] args) throws IOException {

            Properties configProperties = ConfigLoader.loadConfig();
            String INDEX_PATH = configProperties.getProperty("index.path", "index");
            String TEXT_PATH = configProperties.getProperty("text.path", "text");

            // Path to the folder containing text files
            Path docDir = Paths.get(TEXT_PATH);
            
            // Path to the folder where the Lucene index will be stored
            Path path = Paths.get(INDEX_PATH);
            Directory directory = FSDirectory.open(path);

            // Create an IndexWriter configuration with a standard analyzer
            IndexWriterConfig config = new IndexWriterConfig(new StandardAnalyzer());
            config.setCodec(new SimpleTextCodec());
            config.setOpenMode(IndexWriterConfig.OpenMode.CREATE); // Substitute existing index

            long startTime = System.nanoTime();

            // Try-with-resources to automatically close the IndexWriter
            try (IndexWriter writer = new IndexWriter(directory, config);) {

                // Try-with-resources to automatically close the stream of files
                try (Stream<Path> files = Files.list(docDir)) {
                    files.filter(Files::isRegularFile).filter(p -> p.toString().endsWith(".txt")).forEach(txtpath -> {
                        String fileName = txtpath.getFileName().toString(); // File name
                        try {
                            String content = Files.readString(txtpath);  // File content
                            Document doc = new Document();
                            doc.add(new StringField("nome", fileName, Field.Store.YES));
                            doc.add(new TextField("contenuto", content,Field.Store.YES));
                            writer.addDocument(doc);
                            System.out.println("File name: " + fileName);
                            System.out.println("Content:\n" + content+"\n");
                        } catch (IOException e) {
                            System.err.println("Error reading file " + fileName);
                        }
                    });
                } catch (IOException e) {
                    System.err.println("Error emptying index folder: " + e.getMessage());
                }
                

                // Adding two sample documents
                Document doc1 = new Document();
                doc1.add(new StringField("nome", "Come diventare un ingegnere dei dati, Data Engineer?", Field.Store.YES));
                doc1.add(new TextField("contenuto", "Sembra che oggigiorno tutti vogliano diventare un Data Scientist  ...",Field.Store.YES));
                Document doc2 = new Document();
                doc2.add(new StringField("nome", "Curriculum Ingegneria dei Dati - Sezione di Informatica e Automazione", Field.Store.YES));
                doc2.add(new TextField("contenuto", "Curriculum. Ingegneria dei Dati. Laurea Magistrale in Ingegneria Informatica ...", Field.Store.YES));
                writer.addDocument(doc1);
                writer.addDocument(doc2);

                writer.commit();

                // Measure end time and print indexing duration
                long endTime = System.nanoTime();
                System.out.println("Indexing completed in " + (endTime - startTime) / 1_000_000 + " ms");
            }
    }
}
