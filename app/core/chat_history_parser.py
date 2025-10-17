from app import logger



def chat_history_parser(chat_history, company_code):
    """
    {
        "role": "",
        "content" : "",  # 발화 또는 답변
        "answer_type" : ""        
    }
    """
    converted_history = []

    for history in chat_history:
        for key in history:
            value = history.get(key)

            if key == "user":
                converted_history.append({
                    "role": key,
                    "content": value,
                    "answer_type": ""
                })

            elif key == "agent" and isinstance(value, dict):
                responses = value.get("responses", [])
                if isinstance(responses, list) and len(responses) > 1:
                    custom = responses[1].get("custom", {})
                    data = custom.get("data", {})

                    answer = data.get("answer")
                    answer_type = data.get("answer_type")

                    converted_history.append({
                        "role": key,
                        "content": answer,
                        "answer_type": answer_type
                    })

    return converted_history
