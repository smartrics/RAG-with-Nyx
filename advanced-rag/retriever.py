import openai
import json
from nyx_client import NyxClient, Data
from nyx_client.client import SparqlResultType
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
                    
            category_filter = "FILTER(?theme IN (" + ", ".join(f'"{cat}"' for cat in categories) + "))"
            genre_filter = "FILTER(?type IN (" + ", ".join(f'"{gen}"' for gen in genres) + "))"

            # Combine the SPARQL query
            sparql_query = f"""
            SELECT DISTINCT ?subject ?predicate ?object
            WHERE {{
                ?subject ?predicate ?object .
                ?subject <http://www.w3.org/ns/dcat#theme> ?theme .
                ?subject <http://purl.org/dc/terms/type> ?type .
                {category_filter}
                {genre_filter}
            }}
            """
            s = self._nyx_client.sparql_query(query=sparql_query, local_only=True, result_type=SparqlResultType.SPARQL_CSV)
            results: Data = self.parse_data(s)
            logger.debug(f"Found search results: #{len(results)}")
            print(f"Found {len(results)} results:" )
            for u in results:
                u: Data = u
                print(f"'{u.title}' created by '{u.creator}', size={u.size}b: {u.description[:50]}...")

            return results

        except Exception as e:
            logger.error(f"Error during Nyx search: {e}")
            return []
        
        
    def parse_data(self, raw_data: str) -> list[Data]:
        temp_data_map = {}
        org = self._nyx_client.org
        for line in raw_data.strip().split("\n"):
            subject, predicate, obj = line.split(",", 2)
            subject = subject.strip()
            predicate = predicate.strip()
            obj = obj.strip().strip('"')

            # Initialize a temporary dictionary for the subject if not already present
            if subject not in temp_data_map:
                temp_data_map[subject] = {
                    "name": "",
                    "title": "",
                    "description": "",
                    "org": org,
                    "url": "",
                    "content_type": "",
                    "creator": "",
                    "categories": [],
                    "genre": "",
                    "size": 0,
                }

            # Map predicates to temporary dictionary fields
            if predicate == "http://data.iotics.com/pnyx#productName":
                temp_data_map[subject]["name"] = obj
            elif predicate == "http://purl.org/dc/terms/title":
                temp_data_map[subject]["title"] = obj
            elif predicate == "http://purl.org/dc/terms/description":
                temp_data_map[subject]["description"] = obj
            elif predicate == "http://purl.org/dc/terms/creator":
                temp_data_map[subject]["creator"] = obj
            elif predicate == "http://www.w3.org/ns/dcat#theme":
                temp_data_map[subject]["categories"].append(obj)
            elif predicate == "http://purl.org/dc/terms/type":
                temp_data_map[subject]["genre"] = obj
            elif predicate == "http://www.w3.org/ns/dcat#byteSize":
                temp_data_map[subject]["size"] = int(obj)
            elif predicate == "http://www.w3.org/ns/dcat#accessURL":
                temp_data_map[subject]["url"] = obj + f"?buyer_org={org}"
            elif predicate == "http://www.w3.org/ns/dcat#mediaType":
                temp_data_map[subject]["content_type"] = obj
                if obj.startswith("http"):
                    temp_data_map[subject]["content_type"] = obj.split("/")[-1]


        # Construct immutable Data objects
        data_objects = [
            Data(
                name=data["name"],
                title=data["title"],
                description=data["description"],
                org=data["org"],
                url=data["url"],
                content_type=data["content_type"],
                creator=data["creator"],
                categories=data["categories"],
                genre=data["genre"],
                size=data["size"],
                custom_metadata=[],
                connection_id=None
            )
            for data in temp_data_map.values()
        ]
        return data_objects
