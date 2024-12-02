import os
from dotenv import load_dotenv

load_dotenv()

# Configuration settings
WAKE_WORD = "hey athena"
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
VOICE_RATE = 150
VOICE_VOLUME = 1.0
FEMALE_VOICE_ID = 1  # Usually 1 is female voice in Windows