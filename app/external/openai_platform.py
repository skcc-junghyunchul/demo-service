import config as config
import requests
import json
import time
from openai import OpenAI
from openai.types.chat import ChatCompletionMessage
from openai import BadRequestError
from app import logger
from app.models.message import Message

async def query_openai(user_question, llm_resource_value, company_code, message:Message):
    
    
    resource_value_dict = json.loads(llm_resource_value['resource_value'])
    
    A_X_API_URL = resource_value_dict.get('A_X_API_URL')
    A_X_API_KEY = resource_value_dict.get('A_X_API_KEY')
    A_X_GEM_MODEL_NAME = resource_value_dict.get('A_X_GEM_MODEL_NAME')
    A_X_APP_ID = message.aip_app_id
    A_X_CHAT_ID = message.aip_chat_id
    A_X_COMPANY = company_code
    A_X_DEPARTMENT = message.aip_department
    A_X_USER = message.user_id
    A_X_TRANSACTION_ID = message.aip_transaction_id

    # logger.info(f"A_X_API_URL Value: {A_X_API_URL}",extra={"tenant":company_code})
    # logger.info(f"A_X_API_KEY Value: {A_X_API_KEY}",extra={"tenant":company_code})
    # logger.info(f"A_X_GEM_MODEL_NAME Value: {A_X_GEM_MODEL_NAME}",extra={"tenant":company_code})
    # logger.info(f"A_X_APP_ID Value: {A_X_APP_ID}",extra={"tenant":company_code})
    # logger.info(f"A_X_CHAT_ID: {A_X_CHAT_ID}",extra={"tenant":company_code})
    # logger.info(f"A_X_COMPANY: {A_X_COMPANY}",extra={"tenant":company_code})
    # logger.info(f"A_X_DEPARTMENT: {A_X_DEPARTMENT}",extra={"tenant":company_code})
    # logger.info(f"A_X_USER: {A_X_USER}",extra={"tenant":company_code})
    # logger.info(f"A_X_TRANSACTION_ID: {A_X_TRANSACTION_ID}",extra={"tenant":company_code})
    
    
    client = OpenAI(
        base_url=A_X_API_URL,
        api_key=A_X_API_KEY
    )


    # messages = [
    #     {"role": "system", "content": "You are an AI assistant that categorizes user questions."},
    #     {"role": "user", "content": (
    #         f"If the following question: '{user_question}' is related to daily casual conversations,"
    #         "please return the result as a JSON object: {\"category\": \"chitchat\"}. "
    #         "If the question is related to IT Helpdesk inquiries, such as inquiries about technical issues,"
    #         "IT devices, or other work-related matters like working hours, company standards, labor standards,"
    #         "office rules, leave rules, or work from home rules, return the result as a JSON object: {\"category\": \"helpdesk\"}."
    #         "If the question is related to the use of SK Telecom's Adotbiz(synonyms: 에이닷비즈, adotbiz, a.biz, Adotbiz) solution which includes serivces such as News Creation, Meeting Room Reservation, Company's Public Relations, Law Clause Search that help users on their company work tasks using generative AI technology,"
    #         "return the result as a JSON object: {\"category\": \"adotbiz\"}."
    #         "Only respond with a valid JSON object."
    #     )}
    # ]


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


    try:
        chat_completion = client.chat.completions.create(
            model = A_X_GEM_MODEL_NAME,
            messages = messages,
            temperature=0.0,
            max_tokens=100,
            tools=None,
            tool_choice=None,
            extra_headers={"aip-app-id" :A_X_APP_ID, 
            "aip-chat-id" : A_X_CHAT_ID,
            "aip-company" : A_X_COMPANY,
            "aip-department" : A_X_DEPARTMENT,
            "aip-user" : A_X_USER,
            "aip-transaction-id" : A_X_TRANSACTION_ID,
            },
        )
        

        
    except BadRequestError as bre:
        raise ContentFilteringError


    # logger.info(f"=====LLM_token_usage=====: {chat_completion.usage}",extra={"tenant":company_code})
    
    return chat_completion.choices[0].message.content

