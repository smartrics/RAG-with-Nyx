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
        