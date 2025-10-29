import aiohttp
from typing import Dict, Text, Any
import config
import ssl
import certifi
import json
import zlib
import os
import logging
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RAG_API_URL = config.RAG_API_URL  # Ensure this URL is correct
RAG_INDEX_PATH = config.RAG_INDEX_PATH  # Path to the RAG index file

MAX_PAYLOAD_SIZE = 1024 * 1024  # 1 MB

# Ensure the RAG index file is present and accessible
if not os.path.exists(RAG_INDEX_PATH):
    raise FileNotFoundError(f"RAG index file not found at path: {RAG_INDEX_PATH}")
if not os.access(RAG_INDEX_PATH, os.R_OK):
    raise PermissionError(f"RAG index file is not accessible at path: {RAG_INDEX_PATH}")

# Validate RAG_API_URL
if not RAG_API_URL or not RAG_API_URL.startswith("http"):
    raise ValueError(f"Invalid RAG_API_URL: {RAG_API_URL}")

# Load and create an index for faster search
def load_rag_index():
    try:
        with open(RAG_INDEX_PATH, 'r') as index_file:
            data = json.load(index_file)
            index = defaultdict(list)
            for item in data.get("documents", []):
                for word in item.get("content", "").split():
                    index[word.lower()].append(item)
            logger.info("RAG index successfully loaded and indexed.")
            return index
    except Exception as e:
        logger.error(f"Error loading RAG index: {e}")
        raise

rag_index = load_rag_index()

async def call_rag_api(
        query_params: Dict[Text, Any] = {},
        body: Dict[Text, Any] = {}
    ):
    headers = {
        "Content-Type": "application/json",
        "Connection": "Keep-Alive",
        "X-Cache-Inf": "caching"
    }
    
    method_type = "post"

    # Create SSL context
    ssl_context = ssl.create_default_context()
    ssl_context.load_verify_locations(certifi.where())

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
        method = getattr(session, method_type)
        try:
            async with method(
                url=RAG_API_URL,
                json=body,
                params=query_params,
                headers=headers,
                verify=certifi.where()  # Explicitly verify SSL certificate
            ) as resp:
                response_data = await resp.json()
                
                # Log API response
                logger.info(f"API Response: {response_data}")
                
                # Check payload size
                response_size = len(json.dumps(response_data).encode('utf-8'))
                if response_size > MAX_PAYLOAD_SIZE:
                    # Compress the response if it exceeds the maximum size
                    compressed_data = zlib.compress(json.dumps(response_data).encode('utf-8'))
                    logger.info("Response compressed due to size limit.")
                    return {
                        "compressed": True,
                        "compression_method": "zlib",
                        "original_size": response_size,
                        "data": compressed_data
                    }
                
                # Handle edge case for empty results
                if not response_data.get("results"):
                    raise ValueError("RAG results cannot be empty.")
                
                return response_data
        except Exception as e:
            logger.error(f"Error during API call: {e}")
            return {"error": str(e)}

# New function to perform indexed search
def search_with_index(query: str):
    words = query.lower().split()
    results = []
    for word in words:
        results.extend(rag_index.get(word, []))
    if not results:
        logger.warning("No results found in the index.")
    return results

# Example usage of the indexed search
if __name__ == "__main__":
    query = "example search term"
    indexed_results = search_with_index(query)
    logger.info(f"Indexed search results: {indexed_results}")