import aiohttp
from typing import Dict, Text, Any
import config
import ssl
import certifi

RAG_API_URL = config.RAG_API_URL  # Ensure this URL is correct


async def call_rag_api(
        query_params: Dict[Text, Any] = {},
        body: Dict[Text, Any] = {}
    ):
        headers ={
            "Content-Type" : "application/json",
            "Connection" : "Keep-Alive",
            "X-Cache-Inf" : "caching"
        }
        
        method_type = "post"

        async with aiohttp.ClientSession() as session:
            method = getattr(session, method_type)
            async with method(
                url=RAG_API_URL,
                json=body,
                params=query_params,
                headers=headers
            ) as resp:
                return await resp.json()
