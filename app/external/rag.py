import aiohttp
from typing import Dict, Text, Any
import config
import ssl
import certifi
import json
import zlib
import os

RAG_API_URL = config.RAG_API_URL  # Ensure this URL is correct
RAG_INDEX_PATH = config.RAG_INDEX_PATH  # Path to the RAG index file

MAX_PAYLOAD_SIZE = 1024 * 1024  # 1 MB

# Ensure the RAG index file is present and accessible
if not os.path.exists(RAG_INDEX_PATH):
    raise FileNotFoundError(f"RAG index file not found at path: {RAG_INDEX_PATH}")
if not os.access(RAG_INDEX_PATH, os.R_OK):
    raise PermissionError(f"RAG index file is not accessible at path: {RAG_INDEX_PATH}")

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
        async with method(
            url=RAG_API_URL,
            json=body,
            params=query_params,
            headers=headers
        ) as resp:
            response_data = await resp.json()
            
            # Check payload size
            response_size = len(json.dumps(response_data).encode('utf-8'))
            if response_size > MAX_PAYLOAD_SIZE:
                # Compress the response if it exceeds the maximum size
                compressed_data = zlib.compress(json.dumps(response_data).encode('utf-8'))
                return {"compressed": True, "data": compressed_data}
            
            return response_data