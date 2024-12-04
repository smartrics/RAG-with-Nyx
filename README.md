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

def infer_categories_and_genres(genres: list[str], categories: list[str], query: str, model: str = "gpt-4o-mini") -> dict:
    """
    Uses an openai model (default "gpt-4o-mini") to infer categories and genres from the user query.
    
    Args:
        genres (list[str]): A list of genres to choose from
        categories (list[str]): A list of categories to choose from
        query (str): The user's free-text query.
        model (str): The model (default "gpt-4o-mini").

    Returns:
        dict: A dictionary with inferred categories and genres.
    """
    try:
        # Example prompt for gpt4o mini
        prompt = f"""
        
        Extract zero or more categories and zero or more genres from the following query;
        use the provided genres and categories only:
        Genres: [{genres}]
        Categories: [{categories}]
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
```

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

```