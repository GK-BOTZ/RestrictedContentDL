# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
from pymongo import MongoClient
from config import DATABASE_URL
from utils import LOGGER

# Log the initialization attempt
LOGGER.info("Creating Database Client From DATABASE_URL")

try:
    # Create MongoDB client using DATABASE_URL from config.py
    mongo_client = MongoClient(DATABASE_URL)
    # Access the "ItsSmartTool" database
    db = mongo_client["ItsSmartTool"]
    prem_plan1 = db["prem_plan1"]
    prem_plan2 = db["prem_plan2"]
    prem_plan3 = db["prem_plan3"]
    user_sessions = db["user_sessions"]
    LOGGER.info("Database Client Successfully Created!")
except Exception as e:
    # Log the error with details and raise it to halt execution
    LOGGER.error(f"Database Client Create Error: {e}")
    raise