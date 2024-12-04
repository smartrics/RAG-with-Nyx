from loguru import logger
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize logging
logger.add("chatbot.log", rotation="1 MB", level="DEBUG")
