from indexer import index_files
from searcher import search_files

def main():

    # Main loop 
    while True:
        print("\nElasticsearch Text File Manager")
        print("0 - Exit")
        print("1 - Index files")
        print("2 - Search files")
        choice = input("\nSelect an option: ").strip()

        # Handle user choice
        if choice == "0":
            print("Exiting the program\n")
            break

        elif choice == "1":
            print("Starting indexing...")
            index_files()

        elif choice == "2":
            print("Starting search...")
            search_files()

        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
