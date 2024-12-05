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

### Analysing the downloaded data

#### Add File Analysis Functionality
We’ll use pandas to load and process CSV files, combined with GPT-4 for natural language analysis.

Import `pandas`:

```python
import pandas as pd
```

add this file

```python
def analyze_csv_files(files: list[str], query: str, model: str = "gpt-4") -> str:
    """
    Analyze CSV files using GPT-4 to answer a specific query or summarize content.

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
    
```

change the `main()` flow

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
            print("\nYou can now ask specific questions about the downloaded files.")
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
```

## Enhancements for Future Development
The current implementation of the Chatbot can be extended with the following advanced features to improve its functionality, robustness, and versatility:

### Sophisticated Metadata Querying with SPARQL
Nyx offers the ability to retrieve data using advanced querying of associated metadata via SPARQL. Instead of relying solely on inferred genres and categories, the chatbot could:

Leverage the LLM to dynamically generate WHERE clauses for a predefined SPARQL SELECT query.
Enable fine-grained filtering of datalinks based on metadata attributes, such as timestamps, geographical regions, or data provenance.
Example Enhancement: Use the user query to construct a SPARQL query like:
```sparql
SELECT ?dataLink WHERE {
  ?dataLink nyx:category "sales".
  ?dataLink nyx:region "Europe".
  ?dataLink nyx:format "text/csv".
}
```
This approach allows more precise discovery and retrieval of datasets beyond simple keyword matches.

### Enhanced Content Metadata Filtering
In addition to structural metadata (file description, genre, categories, etc.), further refinements could be made by filtering based on content metadata, which describes the actual data within files:

- *Column-Level Metadata*: Filter datasets based on column descriptions, such as requiring a dataset to contain specific fields like "Revenue," "Timestamp," or "Region."
- *Timestamps and Temporal Data*: Use temporal metadata to limit datasets to a specific time range, ensuring relevance for time-sensitive queries.
- *Semantic Validation*: Match datasets whose content aligns with user-defined criteria, such as numeric ranges, categorical values, or semantic descriptions of the data.
This additional layer of filtering provides more relevant and targeted datasets, allowing for deeper and more accurate analyses and reduction of costs.

### Validation of Results Using Knowledge Graphs or Additional LLMs
To ensure the accuracy and relevance of analysis results, the chatbot could incorporate a validation layer:

- *Knowledge Graph Integration*: Validate results against a domain-specific knowledge graph. For example:
    - Cross-check calculated values with known standards or published data.
    - Detect inconsistencies or anomalies in the analysis results.
- *Second-Layer LLM Validation*:
    - Use a secondary LLM to review and score the accuracy and consistency of the primary LLM’s response.
    - Incorporate accuracy scoring into the response, with the chatbot flagging uncertain results for further review by the user.
- *User-Feedback Loop*:
    - Allow users to provide feedback on validation results to improve future accuracy dynamically.

### Better Error Handling with Human-in-the-Loop
To improve reliability and user trust, the chatbot can incorporate human validation in its workflows:

- *Confirmation Prompts*: After generating queries or inferred results, the chatbot should present them to the user for validation before executing critical actions, such as searching or retrieving files.
- *Error Recovery*: For ambiguous responses or failed operations, the chatbot could:
    - Provide clear explanations of errors.
    - Suggest possible fixes or alternative actions.
    - Prompt the user for clarification when required.

### Enhanced Validation to Prevent Vulnerabilities
Stronger validation mechanisms should be implemented to safeguard against issues like invalid inputs, prompt injection, or unintended responses:

- *Input Sanitization*: Validate and sanitize user inputs to prevent harmful or malformed data from influencing the chatbot's behavior.
- *Prompt Validation*: Apply rigorous validation to ensure generated prompts and responses align with predefined rules and constraints.
- *Test Coverage*: Implement unit tests for critical functions, including SPARQL generation, file retrieval, and prompt construction, to catch potential issues early.

### Support for Multimodal Data
Expand the chatbot to handle diverse data types beyond CSV files, making it suitable for multimodal datasets:

1. Supported Formats:
    - JSON
    - XML
    - Images
    - Videos
    - Sensor data streams
2. Unified Analysis:
    - Use the LLM to describe, compare, and correlate data from different modalities.
    - For instance, integrate CSV-based sales data with geospatial information from JSON or sensor readings for a richer analysis.
