# Building a Simple RAG Chatbot with Nyx and OpenAI: A Step-by-Step Guide

Retrieval-Augmented Generation (RAG) is a powerful way to combine external data retrieval with the capabilities of large language models (LLMs). In this blog post, we’ll walk through building a simple RAG chatbot that uses the Nyx Exchange for data retrieval and OpenAI's models for analysis.

We’ll focus on three key aspects:

- Outer and Inner Loops: Structuring the chatbot for dynamic queries and iterative analysis.
- Nyx Data Retrieval: Using inferred metadata to fetch datalinks relevant to the user’s query.
- LLM Integration: Leveraging OpenAI models to answer specific questions or summarise data.

## Overview of the Chatbot

The chatbot:
- Accepts a user query and determines the Genre and Categories of datalinks needed.
- Fetches the relevant datalinks from Nyx based on the inferred metadata.
- Analyses the retrieved datalinks using an LLM to answer the query.
- Enters an inner loop where users can ask additional questions about the data.

This setup ensures an interactive experience, allowing the chatbot to provide contextual answers iteratively.

## Outer and Inner Loops
The chatbot operates in two nested loops:

*- **Outer Loop**: Captures the user's initial query, retrieves relevant data, and performs the first analysis.
- **Inner Loop**: Enables iterative follow-up questions about the retrieved data.

Here’s how the chatbot handles these loops:

```python
def main():
    genres = nyx_client.genres()
    categories = nyx_client.categories()
    downloaded_files = []

    while True:  # Outer Loop
        user_query = input("\nEnter your query: ").strip()
        if user_query.lower() == 'exit':
            print("Goodbye!")
            break

        # Infer genres and categories
        inferred = infer_categories_and_genre(genres, categories, user_query)

        # Retrieve matching datalinks
        matching_datalinks = search_nyx_for_files(nyx_client, inferred['categories'], inferred['genres'])
        if not matching_datalinks:
            print("No matching datalinks found.")
            continue

        # Download files
        downloaded_files = retrieve_csv_files(nyx_client, matching_datalinks)

        # Initial analysis of the user query
        print("Initial Analysis:")
        print(analyse_csv_files(downloaded_files, user_query))

        # Inner Loop for follow-up questions
        while True:
            follow_up_query = input("\nAsk another question about the data, or type 'exit': ").strip()
            if follow_up_query.lower() == 'exit':
                downloaded_files = []  # Clear for a new query
                break

            print("Analysis Result:")
            print(analyse_csv_files(downloaded_files, follow_up_query))

```
Key Points:
- Outer Loop: Handles new queries, file retrieval, and initial analysis.
- Inner Loop: Allows iterative questioning of the retrieved data.

## Data Retrieval with Nyx

The chatbot uses Nyx SDK to retrieve datalinks based on the inferred metadata from the user query. Here’s how the retrieval process works:

### Search for Matching DataLinks

The chatbot searches for datalinks using the inferred *Genre* and *Categories*:

```python
def search_nyx(client, categories, genres):
    results = []
    for c in categories:
        for g in genres:
            results.extend(client.get_data(categories=[c], genre=g, content_type="text/csv"))

    # Remove duplicates and return unique results
    return {f"{res.name}-{res.creator}": res for res in results}.values()
```

### Download Files
Once the files are identified, the chatbot downloads them for analysis:

```python
def retrieve_csv_files(client, data, download_path="./data"):
    os.makedirs(download_path, exist_ok=True)
    downloaded_files = []
    for d in data:
        client.subscribe(d)
        file_path = os.path.join(download_path, d.name)
        with open(file_path, "wb") as file:
            file.write(d.as_string())
        downloaded_files.append(file_path)
    return downloaded_files
```

## Interaction with the LLM
The chatbot uses OpenAI models to analyse the downloaded data. Depending on the user’s query, it either:

- Answers a specific question, or
- Generates a summary of the data if the query is vague.

Here’s how the chatbot integrates the LLM for analysis:

```python
def analyse_csv_files(files, query, model="gpt-4"):
    # Combine data from all files
    dataframes = [pd.read_csv(file) for file in files]
    combined_data = pd.concat(dataframes)

    # Prepare the prompt
    summary = combined_data.describe().to_string()
    prompt = f"Data summary:\n{summary}\nUser query: {query}"

    # Call the OpenAI model
    response = openai.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    return response.choices[0].message.content.strip()
```

Example:

1. User Query: "Show me sales data for Europe."
    - The chatbot retrieves relevant datalinks from Nyx and provides an initial analysis.
2. Follow-Up Question: "What are the top-selling products?"
    - The chatbot analyses the retrieved data and answers the question using the LLM.

## Conclusion
This RAG chatbot demonstrates the power of combining Nyx for precise data retrieval with OpenAI's models for insightful analysis. 
While the example focuses on Genres and Categories, it lays the groundwork for more advanced use cases, including:

- Fine-grained metadata filtering that leverages Nyx Federated Knowledge Graph accessible via SPARQL.
- Support for multimodal datasets (e.g., JSON, images).
- Enhanced validation using secondary LLMs or knowledge graphs.
