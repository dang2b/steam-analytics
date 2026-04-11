import os
from dotenv import load_dotenv

load_dotenv()

STEAM_API_KEY = os.getenv('STEAM_API_KEY')
STEAM_USER_ID = os.getenv('STEAM_USER_ID')