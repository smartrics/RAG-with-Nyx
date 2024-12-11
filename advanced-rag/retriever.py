import openai
import json
import csv
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
                    
                Genres: {self._known_genres}
                Categories: {self._known_categories}
                Query: "{query}"  
                
                Provide the response in JSON format with 'explanation', 'categories' and 'genres' as keys.  
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

            print(f"cat = {category_filter}")
            print(f"gen = {category_filter}")

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
            results: Data = self._parse_data(s)
            logger.debug(f"Found search results: #{len(results)}")
            print(f"Found {len(results)} results:" )
            for u in results:
                u: Data = u
                print(f"'{u.title}' created by '{u.creator}', size={u.size}b: {u.description[:50]}...")

            return results

        except Exception as e:
            logger.error(f"Error during Nyx search: {e}")
            return []
        
        
    def _parse_data(self, raw_data: str) -> list[Data]:
        temp_data_map = {}
        org = self._nyx_client.org
        # Read CSV data
        csv_reader = csv.reader(raw_data.strip().split("\n"))
        next(csv_reader) # Excludes the header
        for row in csv_reader:
            if len(row) < 3:
                continue  # Skip malformed rows
            subject, predicate, obj = row[0].strip(), row[1].strip(), row[2].strip()

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
                temp_data_map[subject]["url"] = obj
            elif predicate == "http://www.w3.org/ns/dcat#mediaType":
                temp_data_map[subject]["content_type"] = obj

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
            )
            for data in temp_data_map.values()
        ]

        return data_objects
