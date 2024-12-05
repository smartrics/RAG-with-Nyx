# RAG with Nyx

This sameple project shows a simple RAG application with Nyx. It uses LangChain to perform basic analysis of a CSV file using Nyx as the files repository of data and metadata.

## Flow

### Setup

#### Create virtual environment and activate it

```
cd rag-with-nyx
python -m venv .venv
.venv\Script\activate # source .venv/bin/activate in Linux
```

#### Install dependencies

Required dependencies:
- nyx-client
- openai
- python-dotenv
- loguru

```
pip install -r requirements.txt
```

#### Project structure 

```
rag-with-nyx/
├── .venv/  # Virtual environment (not committed to version control)
├── .env  # Nyx client configuration
├── requirements.txt  # Dependencies
├── README.md  # Project documentation
└── chatbot.py  # Main chatbot script
```

#### Logging

The chatbot.py file is

```python
from loguru import logger
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize logging
logger.remove()
logger.add(sys.stderr, level="ERROR") ## prints on console only errors
logger.add("chatbot.log", rotation="1 MB", level="DEBUG")
```

Run it and an empty log file is created `python chatbot.py`

#### Nyx Client

Access to Nyx is configured by creating a `.env` file and setting the following variables

```bash
NYX_URL=<your Nyx instance endpoint>
NYX_EMAIL=<your Nyx email>
NYX_PASSWORD=<your Nyx password>
```

The chatbot then creates the Nyx client and tests the configuration:

```python
from loguru import logger
import os
from dotenv import load_dotenv
from nyx_client import NyxClient

# Load environment variables
load_dotenv()

# Initialize logging
logger.remove() ## removes default handler that prints everything on console
logger.add(sys.stderr, level="ERROR") ## prints on console only errors
logger.add("chatbot.log", rotation="1 MB", level="DEBUG")

nyx_client = NyxClient()
logger.info("Nyx client initialized.")

print(nyx_client.config)
```

Running `python chatbot.py` produces a log message and the printout of the config in the `.env`

### Main loop

The main loop of the chatbot is an infinite loop where the user is invited to type a question. If the user types `exit` the loop exits and chatbot terminates.

```python
from loguru import logger
import os, sys
from dotenv import load_dotenv
from nyx_client import NyxClient

# Load environment variables
load_dotenv()

# Initialize logging
logger.remove()
logger.add(sys.stderr, level="ERROR") ## prints on console only errors
logger.add("chatbot.log", rotation="1 MB", level="DEBUG")

nyx_client = NyxClient()
logger.info("Nyx client initialized.")

def main():
    """
    Main function to handle user queries interactively.
    """
    logger.info("Starting chatbot...")
    print("Welcome to the CSV Chatbot powered by Nyx!")
    print("Type 'exit' to quit.")

    while True:
        try:
            user_query = input("\nEnter your query: ").strip()
            if user_query.lower() == 'exit':
                print("Goodbye!")
                break

            # Placeholder: Add keyword inference, search, and analysis here
            logger.debug(f"User query received: {user_query}")
            print("Processing your query...")  # Placeholder for future steps

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break

if __name__ == "__main__":
    main()

```

### Inferring genre and categories from the user prompt

We will use an OpenAI model to infer, from the user input, genre and categories to be used to search data in Nyx. Let's add the following to the chatbot.py

#### Import openai library

```python
import openai
import json
```

#### Initialize with Key

After the `load_dotenv()`:

```python
# Initialize OpenAI API (requires OpenAI API key in the .env file)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.error("OpenAI API key missing in .env file.")
    exit(1)

openai.api_key = OPENAI_API_KEY
```

#### New method to infer categories and genre via LLM query

```python

def infer_categories_and_genre(genres: list[str], categories: list[str], query: str, model: str = "gpt-4o-mini") -> dict:
    """
    Uses an openai model (default "gpt-4o-mini") to infer categories and genre from the user query.
    
    Args:
        genres (list[str]): A list of genres to choose from
        categories (list[str]): A list of categories to choose from
        query (str): The user's free-text query.
        model (str): The model (default "gpt-4o-mini").

    Returns:
        dict: A dictionary with inferred categories and genre.
    """
    try:
        # Example prompt for gpt4o mini
        prompt = f"""
        
        Extract zero or more categories and zero or one genre from the following query;
        use the provided genres and categories only:
        Genres: [{genres}]
        Categories: [{categories}]
        Query: "{query}"
        Provide the response in JSON format with 'categories' and 'genre' as keys.
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
        return {"categories": [], "genre": None}
```

#### Integration in the main workflow

Then the `main()` becomes

```python
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

            # Step 1: Infer categories and genre
            inferred_keywords = infer_categories_and_genre(genres=genres, categories=categories, query=user_query)
            print(f"Inferred Categories: {inferred_keywords.get('categories')}")
            print(f"Inferred Genres: {inferred_keywords.get('genres')}")
            
            # Placeholder: Add keyword inference, search, and analysis here
            logger.debug(f"User query received: {user_query}")
            print("Processing your query...")  # Placeholder for future steps

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break

```

### Retrieving data with Nyx

#### Searching Nyx for Matching Files
Add a function to perform a search based on inferred categories and genre

```python
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
```

#### Subscribing to and Retrieving Files
Add a function to subscribe to and download files

```python
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
                file.write(d.as_string())
            logger.info(f"Downloaded file: {file_path}")

            downloaded_files.append(file_path)
        except Exception as e:
            logger.error(f"Error retrieving resource {d.name}: {e}")

    return downloaded_files
```
