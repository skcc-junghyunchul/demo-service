import config as config
import requests
import json
import time
from openai import OpenAI
from openai.types.chat import ChatCompletionMessage
from openai import BadRequestError, OpenAIError
from app import logger
from app.models.message import Message

# Define a constant for API timeout
API_TIMEOUT = 60  # Increased timeout value
MAX_RETRIES = 5  # Increased maximum number of retries

# Define available models
available_models = ["gpt-4", "gpt-4.5"]  # Updated supported models

class ModelNotFoundError(Exception):
    pass

async def query_openai(user_question, llm_resource_value, company_code, message: Message):
    if message is None:
        raise ValueError('Message cannot be None')
    
    resource_value_dict = json.loads(llm_resource_value['resource_value'])
    
    A_X_API_URL = resource_value_dict.get('A_X_API_URL')
    A_X_API_KEY = resource_value_dict.get('A_X_API_KEY')
    A_X_GEM_MODEL_NAME = resource_value_dict.get('A_X_GEM_MODEL_NAME')

    # Verify and update model name or path
    if not A_X_GEM_MODEL_NAME:
        logger.error("Model name is missing in resource_value.")
        raise ValueError("Model name cannot be None or empty.")

    # Validate model availability
    if A_X_GEM_MODEL_NAME not in available_models:
        logger.error(f"Specified model '{A_X_GEM_MODEL_NAME}' is not available. Available models are: {available_models}")
        raise ModelNotFoundError(f"Specified model '{A_X_GEM_MODEL_NAME}' not found.")

    A_X_APP_ID = message.aip_app_id
    A_X_CHAT_ID = message.aip_chat_id
    A_X_COMPANY = company_code
    A_X_DEPARTMENT = message.aip_department
    A_X_USER = message.user_id
    A_X_TRANSACTION_ID = message.aip_transaction_id

    client = OpenAI(
        base_url=A_X_API_URL,
        api_key=A_X_API_KEY,
        timeout=API_TIMEOUT,  # Set timeout
        verify_ssl=False  # Disable SSL verification
    )

    messages = [
        {
            "role": "system",
            "content": "You are an AI assistant that classifies user questions into predefined categories."
        },
        {
            "role": "user",
            "content": (
                f"Classify the following question: '{user_question}'.\n\n"
                "If it is related to casual, everyday conversation, respond with:\n"
                "{\"category\": \"chitchat\"}\n\n"
                "If it concerns IT Helpdesk topics, such as technical issues, IT equipment, or work-related matters "
                "like working hours, company policies, labor standards, office rules, leave, or remote work, respond with:\n"
                "{\"category\": \"helpdesk\"}\n\n"
                "If it relates to SK Telecom's Adotbiz solution (also referred to as 에이닷비즈, adotbiz, a.biz, or Adotbiz), "
                "which includes services like News Creation, Meeting Room Reservation, Company Public Relations, Law Clause Search, or Recruitment, AI Report, Calender Scheduling, and Tax AI"
                "respond with:\n"
                "{\"category\": \"adotbiz\"}\n\n"
                "Respond **only** with a valid JSON object."
            )
        }
    ]

    retries = 0
    while retries < MAX_RETRIES:
        try:
            chat_completion = client.chat.completions.create(
                model=A_X_GEM_MODEL_NAME,
                messages=messages,
                temperature=0.2,  # Optimized temperature for predictable responses
                max_tokens=50,  # Reduced max tokens for optimized usage
                tools=None,
                tool_choice=None,
                extra_headers={
                    "aip-app-id": A_X_APP_ID,
                    "aip-chat-id": A_X_CHAT_ID,
                    "aip-company": A_X_COMPANY,
                    "aip-department": A_X_DEPARTMENT,
                    "aip-user": A_X_USER,
                    "aip-transaction-id": A_X_TRANSACTION_ID,
                },
            )
            return chat_completion.choices[0].message.content
        except BadRequestError as bre:
            logger.error(f"BadRequestError: {bre}")
            raise ContentFilteringError
        except OpenAIError as oe:
            logger.error(f"OpenAIError: {oe}")
            retries += 1
            logger.info(f"Retrying... ({retries}/{MAX_RETRIES})")
            if retries >= MAX_RETRIES:
                raise RuntimeError("An error occurred while querying OpenAI after multiple retries.")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            retries += 1
            logger.info(f"Retrying... ({retries}/{MAX_RETRIES})")
            if retries >= MAX_RETRIES:
                raise RuntimeError("An unexpected error occurred after multiple retries.")