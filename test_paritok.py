import asyncio
import os
from dotenv import load_dotenv

# Load Paritok API Key from .env
load_dotenv()

# Add master-fetch/src to sys.path
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "master-fetch", "src")))

from master_fetch.fetcher import http_get

async def main():
    print(f"Loaded PARITOK_API_KEY: {os.environ.get('PARITOK_API_KEY')}")
    print("Testing master_fetch with Paritok proxy...")
    
    try:
        # Fetching a simple URL to test the connection and headers
        response = await http_get("https://httpbin.org/get")
        print(f"Status Code: {response.status}")
        print("Response Body:")
        print(response.content)
    except Exception as e:
        print(f"Error fetching: {e}")
        print("\nMake sure your Paritok proxy is running on port 8080:")
        print("paritok proxy --port 8080 --config-file j:\Mark-LV\paritok.yaml")

if __name__ == "__main__":
    asyncio.run(main())
