import os
import requests
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

## Testing the API KEy Access
print("Testing Unsplash API Key Access")
access_key = os.getenv("UNSPLASH_ACCESS_KEY")
if not access_key:
    print("UNSPLASH_ACCESS_KEY is not set in the environment variables.")
else:
    print("UNSPLASH_ACCESS_KEY is set.")