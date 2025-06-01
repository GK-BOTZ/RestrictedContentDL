# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
from pymongo import MongoClient
from config import DB_URL
from utils import LOGGER

# Log the initialization attempt
LOGGER.info("Creating DB Client From DB_URL")

try:
    # Create MongoDB client using DB_URL from config.py
    channel_db_client = MongoClient(DB_URL)
    # Access the "ItsSmartTool" database
    channel_db = channel_db_client["ItsSmartTool"]
    daily_limit = channel_db["daily_limit"]
    total_users = channel_db["total_users"]
    LOGGER.info("DB Client Successfully Created!")
except Exception as e:
    # Log the error with details and raise it to halt execution
    LOGGER.error(f"Failed to create DB Client for Group-Channel Bindings: {e}")
    raise