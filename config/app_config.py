# financial_analyzer/config/app_config.py
import os
from dotenv import load_dotenv

load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")
flet_secret_key=os.getenv("FLET_SECRET_KEY")