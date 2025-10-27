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
        if not isinstance(history, dict):
            logger.error(f"Invalid history format: {history}")
            continue  # Skip invalid history entries

        for key in history:
            value = history.get(key)

            if key == "user":
                if not isinstance(value, str):
                    logger.error(f"Invalid user content format: {value}")
                    continue  # Skip invalid user content

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

                    if not isinstance(answer, str) or not isinstance(answer_type, str):
                        logger.error(f"Invalid agent response format: answer={answer}, answer_type={answer_type}")
                        continue  # Skip invalid agent responses

                    converted_history.append({
                        "role": key,
                        "content": answer,
                        "answer_type": answer_type
                    })

    return converted_history
