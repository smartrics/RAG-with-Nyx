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
logger.add("chatbot.log", rotation="1 MB", level="DEBUG")

logger.info("Nyx client initialized.")
```

Run it and an empty log file is created `python chatbot.py`

#### Nyx Client

Access to nyx is configured by creating a `.env` file and setting the following variables

```bash
NYX_URL=<your nyx instance endpoint>
NYX_EMAIL=<your nyx email>
NYX_PASSWORD=<your nyx password>
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
logger.add("chatbot.log", rotation="1 MB", level="DEBUG")

nyx_client = NyxClient()
logger.info("Nyx client initialized.")

print(nyx_client.config)
```