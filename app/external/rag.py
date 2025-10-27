import aiohttp
from typing import Dict, Text, Any
import config
import ssl
import certifi
import json
import zlib

RAG_API_URL = config.RAG_API_URL  # Ensure this URL is correct

MAX_PAYLOAD_SIZE = 1024 * 1024  # 1 MB

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