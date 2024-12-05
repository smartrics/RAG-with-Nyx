import json
import openai
import os
import sys
import pandas as pd
from loguru import logger
from dotenv import load_dotenv
from nyx_client import NyxClient, Data


# Load environment variables
load_dotenv()


# Initialise logging
logger.remove()
logger.add(sys.stderr, level="ERROR") ## prints on console only errors
logger.add("chatbot.log", rotation="1 MB", level="DEBUG")

nyx_client = NyxClient()
logger.info(f"Nyx client initialised; connected to Nyx at {nyx_client.config.nyx_url}")

# Initialise OpenAI API (requires OpenAI API key in the .env file)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.error("OpenAI API key missing in .env file.")
    exit(1)

openai.api_key = OPENAI_API_KEY
def infer_categories_and_genres(genres: list[str], categories: list[str], query: str, model: str = "gpt-4") -> dict:
    """
    Uses an OpenAI model to infer categories and genres from the user query.
    
    Args:
        genres (list[str]): A list of genres to choose from.
        categories (list[str]): A list of categories to choose from.
        query (str): The user's free-text query.
        model (str): The model (default "gpt-4").

    Returns:
        dict: A dictionary with inferred categories and a genres.
    """
    try:
        # Example prompt for gpt-4
        prompt = f"""
        Extract zero or more categories and zero or more genres from the following query;
        Use only the provided genres and categories.
        Genres: {genres}
        Categories: {categories}
        Query: "{query}"
        Provide the response in JSON format with 'categories' and 'genres' as keys.
        """

        logger.debug(f"Sending query to GPT: {query}")

        response = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )

        result = response.choices[0].message.content.strip()
        logger.debug(f"Raw response from GPT: {result}")
        
        # Convert result to a dictionary
        inferred_data = json.loads(result)  # Use a safer JSON parsing method in production
        logger.info(f"Inferred keywords: {inferred_data}")
        return inferred_data

    except Exception as e:
        logger.error(f"Error during keyword inference: {e}")
        return {"categories": [], "genres": []}

def search_nyx_for_files(client: NyxClient, categories: list[str], genres: list[str]) -> list[Data]:
    """
    Searches Nyx for files matching the given categories and genres.

    Args:
        client: The NyxClient instance.
        categories (list[str]): List of inferred categories.
        genres (list[str]): List of inferred genres.

    Returns:
        list: A list of resource IDs for matching files.
    """
    try:
        logger.info(f"Searching Nyx for files with categories: {categories} and genres: {genres}")

        # We search for every combination of genre and categories
        results: Data = []
        for c in categories:
            for g in genres:
                r = client.get_data(categories=[c], genre=g, content_type="text/csv")
                results.extend(r)
        
        # Remove duplicates
        seen = set()
        unique_results = []  
        for data in results:
            key = (data.name, data.creator)  
            if key not in seen:
                seen.add(key)
                unique_results.append(data)
                        
        logger.debug(f"Found search results: #{len(unique_results)}")
        print(f"Found {len(unique_results)} results:" )
        for u in unique_results:
            print(f"'{u.title}' created by '{u.creator}', size={u.size}b: {u.description[:50]}...")

        return unique_results

    except Exception as e:
        logger.error(f"Error during Nyx search: {e}")
        return []

def retrieve_csv_files(client: NyxClient, data: list[Data], download_path: str = "./data") -> list[str]:
    """
    Subscribes to and downloads CSV files from Nyx.

    Args:
        client: The NyxClient instance.
        data (list[Data]): List of resource IDs to download.
        download_path (str): The directory to save downloaded files.

    Returns:
        list: A list of paths to the downloaded CSV files.
    """
    os.makedirs(download_path, exist_ok=True)  # Ensure download directory exists
    downloaded_files = []

    for d in data:
        try:
            logger.info(f"Subscribing to resource: {d.creator}/{d.title}")
            client.subscribe(d)

            # Download the file
            file_path = os.path.join(download_path, f"{d.name}")
            with open(file_path, "wb") as file:
                file.write(d.as_string().encode('utf-8'))
            logger.info(f"Downloaded file: {file_path}")

            downloaded_files.append(file_path)
        except Exception as e:
            logger.error(f"Error retrieving resource {d.name}: {e}")

    return downloaded_files

def analyse_csv_files(files: list[str], query: str, model: str = "gpt-4") -> str:
    """
    Analyse CSV files using GPT-4 to answer a specific query or summarise content.

    Args:
        files (list[str]): List of file paths to the downloaded CSVs.
        query (str): The user's question or query.
        model (str): The OpenAI model to use for analysis.

    Returns:
        str: The analysis result.
    """
    try:
        # Load CSV files into dataframes
        dataframes = []
        for file in files:
            try:
                df = pd.read_csv(file)
                dataframes.append(df)
            except Exception as e:
                logger.error(f"Error loading file {file}: {e}")

        if not dataframes:
            return "No valid data found in the downloaded files."

        # Concatenate all dataframes for analysis
        combined_data = pd.concat(dataframes, ignore_index=True)

        # Prepare the data for GPT-4
        csv_preview = combined_data.head(10).to_string()  # Show a sample of the data
        csv_summary = combined_data.describe(include='all').to_string()  # Summary statistics

        # Construct the GPT-4 prompt
        prompt = f"""
        You are analyzing CSV data. Here is a sample of the data:
        {csv_preview}

        Summary statistics of the data:
        {csv_summary}

        User query: "{query}"

        If the query is specific, answer it based on the data. If the query is generic or not a question,
        provide a summary of the data.
        """

        logger.debug(f"Sending analysis query to GPT: {query}")

        response = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a data analyst."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )

        result = response.choices[0].message.content.strip()
        logger.debug(f"Analysis result: {result}")
        return result

    except Exception as e:
        logger.error(f"Error during CSV analysis: {e}")
        return "An error occurred during analysis. Please try again."
    
def main():
    """
    Main function to handle user queries interactively.
    """
    logger.info("Starting chatbot...")
    print("Welcome to the CSV Chatbot powered by Nyx!")
    print("Type 'exit' to quit.")

    genres = nyx_client.genres()
    categories = nyx_client.categories()
    downloaded_files = []

    while True:
        try:
            if not downloaded_files:
                # Step 1: Get a new query
                user_query = input("\nEnter your query: ").strip()
                if user_query.lower() == 'exit':
                    print("Goodbye!")
                    break

                logger.debug(f"User query received: {user_query}")
                print("Processing your query...")

                # Step 2: Infer categories and genres
                inferred_keywords = infer_categories_and_genres(genres=genres, categories=categories, query=user_query)
                inferred_categories = inferred_keywords.get('categories')
                inferred_genres = inferred_keywords.get('genres')
                print(f"Matched genres: {inferred_genres}, categories: {inferred_categories}")

                # Step 3: Search Nyx for matching files
                matching_files = search_nyx_for_files(
                    client=nyx_client,
                    categories=inferred_categories,
                    genres=inferred_genres,
                )

                if not matching_files:
                    print("No matching files found.")
                    continue

                # Step 4: Retrieve CSV files
                downloaded_files = retrieve_csv_files(client=nyx_client, data=matching_files)

                if downloaded_files:
                    print(f"Downloaded files: {downloaded_files}")
                else:
                    print("No files were downloaded.")
                    continue

            # Step 5: Inner loop for analysis
             # Automatically analyze the initial user query
            print("\nInitial Analysis Result (based on your query):")
            print(analyse_csv_files(downloaded_files, user_query))
            
            print("\nYou can now ask other specific questions about the downloaded files.")
            print("Type 'exit' to finish analyzing the files and return to the main menu.")
            
            while True:
                analysis_query = input("\nEnter your question about the files: ").strip()
                if analysis_query.lower() == 'exit':
                    print("Returning to the main menu...")
                    downloaded_files = []  # Clear the files for a fresh query
                    break

                # Analyse the files
                analysis_result = analyse_csv_files(downloaded_files, analysis_query)
                print("\nAnalysis Result:")
                print(analysis_result)

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        
        
if __name__ == "__main__":
    main()