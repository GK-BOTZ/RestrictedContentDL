# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
# Note: Configure via .env (VPS/local), direct edits to this file (VPS), or Heroku config vars (app.json/dashboard).

import os
from dotenv import load_dotenv

load_dotenv()

def get_env_or_default(key, default=None, cast_func=str):
    """
    Load environment variable with type casting and default value.
    
    Args:
        key (str): Environment variable name
        default: Default value if variable is unset or empty
        cast_func: Function to cast the value (e.g., int, str)
    
    Returns:
        The casted value or default if unset/invalid
    """
    value = os.getenv(key)
    if value is not None and value.strip():
        try:
            return cast_func(value)
        except (ValueError, TypeError) as e:
            print(f"Error casting {key} with value '{value}' to {cast_func.__name__}: {e}")
            return default
    return default

# Telegram API Configuration (Pyrogram MTProto)
API_ID = get_env_or_default("API_ID", "Your_API_ID_Here")
API_HASH = get_env_or_default("API_HASH", "Your_API_HASH_Here")
BOT_TOKEN = get_env_or_default("BOT_TOKEN", "Your_BOT_TOKEN_Here")

# Admin Configuration
DEVELOPER_USER_ID = get_env_or_default("DEVELOPER_USER_ID", "Your_DEVELOPER_USER_ID_Here", int)

# Database Configuration
MONGO_URL = get_env_or_default("MONGO_URL", "Your_MONGO_URL_Here")
DATABASE_URL = get_env_or_default("DATABASE_URL", "Your_DATABASE_URL_Here")
DB_URL = get_env_or_default("DB_URL", "Your_DB_URL_Here")

# Command Prefixes
raw_prefixes = get_env_or_default("COMMAND_PREFIX", "!|.|#|,|/")
COMMAND_PREFIX = [prefix.strip() for prefix in raw_prefixes.split("|") if prefix.strip()]


# Validate Required Variables
required_vars = {
    "API_ID": API_ID,
    "API_HASH": API_HASH,
    "BOT_TOKEN": BOT_TOKEN,
    "DEVELOPER_USER_ID": DEVELOPER_USER_ID,
    "MONGO_URL": MONGO_URL,
    "DATABASE_URL": DATABASE_URL,
    "DB_URL": DB_URL
}

for var_name, var_value in required_vars.items():
    if var_value is None or var_value == f"Your_{var_name}_Here" or (isinstance(var_value, str) and not var_value.strip()):
        raise ValueError(f"Required variable {var_name} is missing or invalid. Set it in .env, config.py, or Heroku config vars.")

# Logging Configuration for Debugging
print(f"Loaded COMMAND_PREFIX: {COMMAND_PREFIX}")
if not COMMAND_PREFIX:
    raise ValueError("No command prefixes found. Set COMMAND_PREFIX in .env, config.py, or Heroku config vars.")