# Simple RAG with Nyx

This sample project demonstrates a simple Retrieval-Augmented Generation (RAG) application. The goal is to illustrate how to perform powerful retrieval operations using the **Nyx Exchange**. It uses OpenAI models to perform basic analysis of a CSV file, with the Nyx Exchange serving as a document repository.

Files are retrieved the Nyx Exchange using a simple search based on Genre and Categories inferred from the user's question. While this approach is simplistic, it effectively demonstrates the mechanics of using the Nyx SDK to perform retrieval operations on files relevant to the user query.

This project highlights the fundamentals of leveraging Nyx as a knowledge repository for contextual data retrieval. For advanced use cases, more sophisticated and metadata-driven methods—such as SPARQL queries or column-level metadata filtering—can be adopted by following the same pattern illustrated here.

## Setup

### Create a virtual environment

Navigate to the project directory and set up a virtual environment:

```
cd rag-with-nyx
python -m venv .venv
.venv\Script\activate # source .venv/bin/activate in Linux
```

### Install dependencies

Add the required dependencies to `requirements.txt`:

- nyx-client
- openai
- python-dotenv
- loguru
- pandas

```
pip install -r requirements.txt
```

### Project structure 

```
rag-with-nyx/
├── .venv/  # Virtual environment
├── .env  # Nyx client configuration
├── requirements.txt  # Dependencies
├── README.md  # Project documentation
└── chatbot.py  # Main chatbot script
```

### Configure Logging

Add logging to `chatbot.py`:

```python
from loguru import logger
import os, sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialise logging
logger.remove()
logger.add(sys.stderr, level="ERROR") ## prints on console only errors
logger.add("chatbot.log", rotation="1 MB", level="DEBUG")
```

Run the script to create an empty log file:

```bash
python chatbot.py
```

## Configuring the Nyx Client

### Setting Up Nyx Credentials

Create a .env file and add the following variables:

```bash
NYX_URL=<your Nyx instance endpoint>
NYX_EMAIL=<your Nyx email>
NYX_PASSWORD=<your Nyx password>
```

### Initialising the Nyx Client

Add the following snippet to `chatbot.py`:

```python
from nyx_client import NyxClient

nyx_client = NyxClient()
logger.info(f"Nyx client initialised; connected to Nyx at {nyx_client.config.nyx_url}")
```

Run the script to confirm the client initialisation by checking the log file:
```bash
python chatbot.py
```

## Main Chatbot Workflow

### Main Loop

The chatbot operates within an infinite loop, inviting the user to ask questions. The loop exits when the user types `exit`:

```python
def main():
    logger.info("Starting chatbot...")
    print("Welcome to the CSV Chatbot powered by Nyx!")
    print("Type 'exit' to quit.")

    while True:
        try:
            user_query = input("\nEnter your query: ").strip()
            if user_query.lower() == 'exit':
                print("Goodbye!")
                break

            logger.debug(f"User query received: {user_query}")
            print("Processing your query...")  
            
            # Placeholder for further steps

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break

if __name__ == "__main__":
    main()

```

## Inferring Genres and Categories

### Integrating OpenAI for Inference

Import the OpenAI library and initialise it with your API key; add the following after the `load_dotenv()` call:

```python
import openai

# Initialise OpenAI API
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.error("OpenAI API key missing in .env file.")
    exit(1)

openai.api_key = OPENAI_API_KEY

```

### Inferring Genres and Categories

Define a function to infer genres and categories from the user query:

```python
import json

def infer_categories_and_genres(genres: list[str], categories: list[str], query: str, model: str = "gpt-4o-mini") -> dict:
    try:
        prompt = f"""
            As an expert data modeller, extract zero or more categories and zero or more genres from the following query.  
            Genres represent the type or subject matter of datasets (e.g., sales, climate, demographics).  
            Categories represent specific topics or domains the data applies to (e.g., healthcare, finance, education).  
            Use only the provided genres and categories below to map the query to categories and genres.  
            Don't expect categories and genres to be explicitly specified in the query but use your ability to infer what they are.  
            If the query includes ambiguous terms or mappings to multiple possible genres or categories, include all plausible options and explain the reasoning behind them.  
            If the query includes contextual filters (e.g., temporal or spatial constraints), note whether these filters influence the inferred genres or categories.  

            Provide an explanation of the thinking process used to determine the results.  
            
            Examples:  
                Query: "Find datasets about sales in Europe for the last 5 years."  
                Genres: ["sales"]  
                Categories: ["finance"]  
                Explanation: "The query explicitly mentions sales, which maps directly to the 'sales' genre. The reference to Europe and the time frame are not specific categories, but 'finance' is inferred based on sales."  

                Query: "Datasets about healthcare in Asia."  
                Genres: ["demographics"]  
                Categories: ["healthcare"]  
                Explanation: "The query explicitly mentions healthcare, which maps to the 'healthcare' category. 'Demographics' is inferred as the genre because healthcare data often relates to population demographics."  
                
            Genres: {genres}  
            Categories: {categories}  
            Query: "{query}"  
            
            Provide the response in JSON format with 'explanation', 'categories' and 'genres' as keys.  
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

### Integration in the main workflow

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

            inferred_keywords = infer_categories_and_genres(genres=genres, categories=categories, query=user_query)
            print(f"Inferred Categories: {inferred_keywords.get('categories')}")
            print(f"Inferred Genres: {inferred_keywords.get('genres')}")
            
            # Placeholder: search and analysis here
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break

```

## Retrieving data with Nyx

### Searching Nyx for DataLinks

Search for files in Nyx based on inferred genres and categories:

```python
from nyx_client import Data

def search_nyx_for_files(client: NyxClient, categories: list[str], genres: list[str]) -> list[Data]:
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

### Downloading Files
Retrieve and save the files locally:

```python
def retrieve_csv_files(client: NyxClient, data: list[Data], download_path: str = "./data") -> list[str]:
    os.makedirs(download_path, exist_ok=True)  # Ensure download directory exists
    downloaded_files = []

    for d in data:
        try:
            logger.info(f"Subscribing to resource: {d.creator}/{d.title}")
            client.subscribe(d)

            # Download the file
            file_path = os.path.join(download_path, f"{d.name}")
            with open(file_path, "wb") as file:
                file.write(d.as_string().encode("utf-8"))
            logger.info(f"Downloaded file: {file_path}")

            downloaded_files.append(file_path)
        except Exception as e:
            logger.error(f"Error retrieving resource {d.name}: {e}")

    return downloaded_files
```

## Analysing Downloaded Data

### Loading and Analysing CSVs

Use pandas and OpenAI GPT for analysis:

```python
import pandas as pd

def analyse_csv_files(files: list[str], query: str, model: str = "gpt-4") -> str:
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
        You are analysing CSV data. Here is a sample of the data:
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

## Final workflow

The chatbot workflow is designed with two nested infinite loops for seamless interaction:

1. Outer Loop: Capturing the Initial Query
    - The chatbot begins by capturing the user’s initial query.
    - This query is used to determine the genres and categories for retrieving relevant files from Nyx.
    - If the query also includes an analysis request, the chatbot immediately processes it via the analysis function and provides a response before entering the second loop.
2. Inner Loop: Follow-Up Analysis on Downloaded Data
    - After the files are downloaded, the chatbot enters a second loop, allowing the user to:
    - Ask additional questions about the already downloaded files.
    - Refine or perform further analysis using the analysis function.
    - The inner loop continues until the user types exit, at which point the chatbot exits the inner loop and returns to the outer loop for new queries.

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
             # Automatically analyse the initial user query
            print("\nInitial Analysis Result (based on your query):")
            print(analyse_csv_files(downloaded_files, user_query))
            
            print("\nYou can now ask other specific questions about the downloaded files.")
            print("Type 'exit' to finish analysing the files and return to the main menu.")
            
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

- **Column-Level Metadata**: Filter datasets based on column descriptions, such as requiring a dataset to contain specific fields like "Revenue," "Timestamp," or "Region."
- **Timestamps and Temporal Data**: Use temporal metadata to limit datasets to a specific time range, ensuring relevance for time-sensitive queries.
- **Semantic Validation**: Match datasets whose content aligns with user-defined criteria, such as numeric ranges, categorical values, or semantic descriptions of the data.
This additional layer of filtering provides more relevant and targeted datasets, allowing for deeper and more accurate analyses and reduction of costs.

### Validation of Results Using Knowledge Graphs or Additional LLMs
To ensure the accuracy and relevance of analysis results, the chatbot could incorporate a validation layer:

- **Knowledge Graph Integration**: Validate results against a domain-specific knowledge graph. For example:
    - Cross-check calculated values with known standards or published data.
    - Detect inconsistencies or anomalies in the analysis results.
- **Second-Layer LLM Validation**:
    - Use a secondary LLM to review and score the accuracy and consistency of the primary LLM’s response.
    - Incorporate accuracy scoring into the response, with the chatbot flagging uncertain results for further review by the user.
- **User-Feedback Loop**:
    - Allow users to provide feedback on validation results to improve future accuracy dynamically.

### Better Error Handling with Human-in-the-Loop
To improve reliability and user trust, the chatbot can incorporate human validation in its workflows:

- **Confirmation Prompts**: After generating queries or inferred results, the chatbot should present them to the user for validation before executing critical actions, such as searching or retrieving files.
- **Error Recovery**: For ambiguous responses or failed operations, the chatbot could:
    - Provide clear explanations of errors.
    - Suggest possible fixes or alternative actions.
    - Prompt the user for clarification when required.

### Enhanced Validation to Prevent Vulnerabilities
Stronger validation mechanisms should be implemented to safeguard against issues like invalid inputs, prompt injection, or unintended responses:

- **Input Sanitisation**: Validate and sanitise user inputs to prevent harmful or malformed data from influencing the chatbot's behavior.
- **Prompt Validation**: Apply rigorous validation to ensure generated prompts and responses align with predefined rules and constraints.
- **Test Coverage**: Implement unit tests for critical functions, including SPARQL generation, file retrieval, and prompt construction, to catch potential issues early.

### Support for Multimodal Data
Expand the chatbot to handle diverse data types beyond CSV files, making it suitable for multimodal datasets:

1. **Supported Formats**:
    - JSON
    - XML
    - Images
    - Videos
    - Sensor data streams
2. **Unified Analysis**:
    - Use the LLM to describe, compare, and correlate data from different modalities.
    - For instance, integrate CSV-based sales data with geospatial information from JSON or sensor readings for a richer analysis.
