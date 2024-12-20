# RAG with Nyx

This repository contains a series of complete examples showcasing the powerful mechanics that [Nyx](NYX.md) offers for data retrieval in Retrieval-Augmented Generation (RAG) applications. These examples demonstrate how Nyx enables sophisticated retrieval capabilities to underpin and enhance RAG workflows.

## Examples in This Repository

### Simple RAG

This example demonstrates a basic chatbot application with a naive implementation of retrieval. It focuses on:

- **Retrieval Method**: Using a simple metadata-based search, where the chatbot identifies relevant datalinks based on Genres and Categories inferred from the user's query.
- **Chatbot Workflow**: Captures user queries, retrieves relevant datalinks from Nyx, and provides responses using OpenAI models.

This example is ideal for understanding the foundational mechanics of Nyx in a RAG context.

### Advanced RAG
This example builds upon the [Simple RAG](#simple-rag) chatbot and introduces enhancements to improve retrieval and user interaction:

- Advanced Search and Discovery:
    - Leverages Nyx's powerful metadata capabilities for fine-grained discovery, including SPARQL-based queries for advanced discovery.
- Human-in-the-Loop Validation:
    - Includes a phase where users validate retrieved documents to ensure relevance and accuracy before they are analysed.
- Enhanced Chatbot Workflow:
    - Supports iterative question-and-answer sessions, allowing users to refine or expand their queries dynamically.
This example demonstrates how Nyx can be used to build robust and interactive RAG applications for production-level scenarios.
