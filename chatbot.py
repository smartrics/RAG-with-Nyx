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