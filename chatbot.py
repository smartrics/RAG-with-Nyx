from loguru import logger
import os, sys
import json
from dotenv import load_dotenv
from nyx_client import NyxClient
import openai


# Load environment variables
load_dotenv()

# Initialize OpenAI API (requires OpenAI API key in the .env file)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.error("OpenAI API key missing in .env file.")
    exit(1)

openai.api_key = OPENAI_API_KEY

# Initialize logging
logger.remove()
logger.add(sys.stderr, level="ERROR") ## prints on console only errors
logger.add("chatbot.log", rotation="1 MB", level="DEBUG")

nyx_client = NyxClient()
logger.info("Nyx client initialized.")

def infer_categories_and_genres(genres: list[str], categories: list[str], query: str, model: str = "gpt-4") -> dict:
    """
    Uses an OpenAI model to infer categories and genres from the user query.
    
    Args:
        genres (list[str]): A list of genres to choose from.
        categories (list[str]): A list of categories to choose from.
        query (str): The user's free-text query.
        model (str): The model (default "gpt-4").

    Returns:
        dict: A dictionary with inferred categories and genres.
    """
    try:
        # Example prompt for gpt-4
        prompt = f"""
        Extract zero or more categories and zero or more genres from the following query:
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

def main():
    """
    Main function to handle user queries interactively.
    """
    logger.info("Starting chatbot...")
    print("Welcome to the CSV Chatbot powered by Nyx!")
    print("Type 'exit' to quit.")

    genres = nyx_client.genres()
    categories = nyx_client.categories()

    while True:
        try:
            user_query = input("\nEnter your query: ").strip()
            if user_query.lower() == 'exit':
                print("Goodbye!")
                break

            # Step 1: Infer categories and genres
            inferred_keywords = infer_categories_and_genres(genres=genres, categories=categories, query=user_query)
            print(f"Inferred Categories: {inferred_keywords.get('categories')}")
            print(f"Inferred Genres: {inferred_keywords.get('genres')}")
            
            # Placeholder: Add keyword inference, search, and analysis here
            logger.debug(f"User query received: {user_query}")
            print("Processing your query...")  # Placeholder for future steps

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break

if __name__ == "__main__":
    main()