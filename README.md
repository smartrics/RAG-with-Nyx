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

#### Main loop

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