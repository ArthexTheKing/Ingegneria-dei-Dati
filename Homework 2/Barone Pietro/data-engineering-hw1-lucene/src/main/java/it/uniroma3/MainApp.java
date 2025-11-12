package it.uniroma3;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;

public class MainApp {
    public static void main(String[] args) throws Exception {
        BufferedReader in = new BufferedReader(new InputStreamReader(System.in));
        boolean running = true;
        System.out.println("\nLucene Search & Index Manager");

        // Main loop
        while (running) {
            System.out.println("\nChoose an option:");
            System.out.println("1 - Index text files (Indexer)");
            System.out.println("2 - Start search (Searcher)");
            System.out.println("0 - Exit");
            System.out.print("> ");

            String choice = in.readLine();

            if (choice == null) {
                break;
            }

            switch (choice.trim()) {
                case "1" -> {
                    System.out.println("\n>>> Starting indexing...\n");
                    try {
                        Indexer.main(new String[]{});  // Call the main method of Indexer
                        System.out.println("\nIndexing completed successfully!");
                    } catch (IOException e) {
                        System.err.println("Error during indexing: " + e.getMessage());
                    }
                }

                case "2" -> {
                    System.out.println("\n>>> Starting search...\n");
                    try {
                        Searcher.main(new String[]{});  // Call the main method of Searcher
                    } catch (Exception e) {
                        System.err.println("Error during search: " + e.getMessage());
                    }
                }

                case "0" -> {
                    System.out.println("\nClosing the program...");
                    running = false;
                }

                default -> System.out.println("\nInvalid choice. Please enter 1, 2, or 0.");
            }
        }

        System.out.println("Program terminated.");
    }
}
