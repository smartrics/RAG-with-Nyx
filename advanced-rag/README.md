# Advanced RAG with Nyx

This tutorial builds on the Simple RAG Chatbot example and introduces a more sophisticated approach to data retrieval using Nyx. The focus is on enhancing the chatbot’s ability to retrieve datalinks from Nyx that are specifically tailored to answer the user’s query.

Before diving into the advanced retrieval techniques, a change has been made to the chatbot code: the retrieval logic has been abstracted into a dedicated Retriever class. This abstraction allows for a more modular code, making it easier to discuss how to extend the retrieval capabilities.

## Enhancements to the Simple RAG Chatbot

### Abstracting Retrieval into a Retriever Class
In the original Simple RAG example, the retrieval process consisted of:

- Inferring genres and categories from the user query.
- Fetching all datalinks in Nyx that match any inferred genre and category.

This workflow has now been refactored into a Retriever class:

```python
import openai
import json
from nyx_client import NyxClient, Data
from loguru import logger

class Retriever:
    
    def __init__(self, nyx_client:NyxClient, model: str = "gpt-4"):
        self._nyx_client: NyxClient = nyx_client
        self._model = model
        self._known_genres: list[str] = nyx_client.genres()
        self._known_categories: list[str] = nyx_client.categories()
        
        
    def retrieve(self, query:str) -> dict:
        inferred_keywords = self._infer_categories_and_genres(query=query)
        inferred_categories = inferred_keywords.get('categories')
        inferred_genres = inferred_keywords.get('genres')
        # Step 3: Search Nyx for matching files
        matching_files = self._search_nyx_for_files(
            categories=inferred_categories,
            genres=inferred_genres,
        )
        return matching_files

        
    def _infer_categories_and_genres(self, query: str) -> dict:
        try:
            prompt = f"""
            Extract zero or more categories and zero or more genres from the following query;
            Use only the provided genres and categories.
            Genres: {self._known_genres}
            Categories: {self._known_categories}
            Query: "{query}"
            Provide the response in JSON format with 'categories' and 'genres' as keys.
            """

            logger.debug(f"Sending query to GPT: {query}")

            response = openai.chat.completions.create(
                model=self._model,
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

    def _search_nyx_for_files(self, categories: list[str], genres: list[str]) -> list[Data]:
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
                    r = self._nyx_client.get_data(categories=[c], genre=g, content_type="text/csv")
                    results.extend(r)
            
            # Remove duplicates
            seen = set()
            unique_results = []  
            for data in results:
                data: Data = data
                key = (data.name, data.creator)  
                if key not in seen:
                    seen.add(key)
                    unique_results.append(data)
                            
            logger.debug(f"Found search results: #{len(unique_results)}")
            print(f"Found {len(unique_results)} results:" )
            for u in unique_results:
                u: Data = u
                print(f"'{u.title}' created by '{u.creator}', size={u.size}b: {u.description[:50]}...")

            return unique_results

        except Exception as e:
            logger.error(f"Error during Nyx search: {e}")
            return []
```

### Integrating the Retriever into the Chatbot

The Retriever is then injected into the main chatbot workflow. The chatbot uses it to handle all retrieval-related logic, simplifying the main workflow.
Here’s how the chatbot integrates the Retriever:

```python
def main():

    ## initialisation

    while True:
        try:
            if not downloaded_files:
                # Step 1: Get a new query
                ## cut ...

                print("Processing your query...")

                matching_files = retriever.retrieve(query=user_query)

                if not matching_files:
                    print("No matching files found.")
                    continue

                # Step 4: Retrieve CSV files
                downloaded_files = retrieve_csv_files(client=nyx_client, data=matching_files)


            # Step 5: Inner loop for analysis
            ## ...

        # ...        
        
if __name__ == "__main__":
    main()
```


## Querying the Nyx catalog

In this section, we enhance the Retriever by leveraging SPARQL for querying the Nyx catalog. SPARQL allows for precise and metadata-driven retrieval of datalinks, making it a perfect fit for building advanced RAG applications.

### Using SPARQL for querying

The Nyx SDK provides an interface to execute SPARQL queries using the sparql method:

```python
s:str = NyxClient().sparql(query="...", local_only=True|False, result_type=...)
```

Parameters:
- query: A SPARQL query string.
- local_only: A Boolean indicating whether the query should run only on the local Nyx instance (True) or be federated across the Nyx network (False).
- result_type: The format of the result, which can be set using the SparqlResultType enum (e.g., SPARQL_CSV, SPARQL_JSON, etc.).

#### Example: Querying Metadata for a Dataset
The following example demonstrates how to retrieve metadata for a specific dataset:

```python
from nyx_client import NyxClient
from nyx_client.client import SparqlResultType

nyx = NyxClient()

query = """SELECT ?subject ?predicate ?object
WHERE {
  ?subject <http://data.iotics.com/pnyx#productName> "simulated-erp-it-dataset-full.csv" .
  ?subject ?predicate ?object .
}
"""

result = nyx.sparql(query=query, local_only=True, result_type=SparqlResultType.SPARQL_CSV)
print(result)
```

This query fetches all metadata associated with the dataset named simulated-erp-it-dataset-full.csv. The result is returned as a CSV file, formatted as:

```csv
subject,predicate,object
did:iotics:iotKbQEZMrFNfkfmLc47GtiR9a3GuZi7MB2L,http://www.w3.org/1999/02/22-rdf-syntax-ns#type,http://www.w3.org/ns/dcat#Dataset
did:iotics:iotKbQEZMrFNfkfmLc47GtiR9a3GuZi7MB2L,http://data.iotics.com/iotics#updatedAt,2024-09-20T11:57:33.669+00:00
did:iotics:iotKbQEZMrFNfkfmLc47GtiR9a3GuZi7MB2L,http://purl.org/dc/terms/title,IT Asset Lifecycle and Performance Data (2015-2024)
...
```

### Retrieving DataLinks by genre and categories

Retrieving DataLinks by Genre and Categories
SPARQL Query for Genres and Categories
To retrieve all datalinks matching inferred Genres `("t1", "t2", "t3")` and Categories `("h1", "h2", "h3")`, the SPARQL query would look like this:

```sql
SELECT DISTINCT ?subject ?predicate ?object
WHERE {
  ?subject ?predicate ?object .
  ?subject <http://purl.org/dc/terms/type> ?type .
  ?subject <http://www.w3.org/ns/dcat#theme> ?theme .
  FILTER(?type IN ("t1", "t2", "t3"))  
  FILTER(?theme IN ("h1", "h2", "h3")) 
}
```
This query finds all datalinks whose metadata matches any combination of the specified genres (`type`) and categories (`theme`).

### Refactoring `_search_nyx_for_files` to Use SPARQL
We can now refactor the Retriever class’s _search_nyx_for_files function to leverage SPARQL for genre and category-based retrieval.

Updated _search_nyx_for_files