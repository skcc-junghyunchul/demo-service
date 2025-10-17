import config as config
import requests
import json
import time

def query_openai(user_question):
    
    ENDPOINT = config.AZURE_OPENAI_ENDPOINT
    API_KEY = config.AZURE_OPENAI_API_KEY


    prompt = (
        f"If the following question: '{user_question}' is related to daily casual conversations, "
        "please return the result as a JSON object: {\"category\": \"chitchat\"}. "
        "If the question is related to IT Helpdesk inquiries, such as inquiries about technical issues, IT devices, or other work-related matters like working hours, company standards, labor standards, office rules, leave rules, work from home rules"
        "return the result as a JSON object: {\"category\": \"helpdesk\"}."
        "Only respond with a valid JSON object."
    )

       
    url = ENDPOINT
    headers = {
        "Content-Type": "application/json",
        "api-key": API_KEY  # Bearer 대신 api-key 사용!
    }
    data = {
        "messages": [{"role": "system", "content": "You are an AI assistant."},
                     {"role": "user", "content": prompt}],
        "temperature": 0.0,
        "max_tokens": 100
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Error {response.status_code}: {response.text}"