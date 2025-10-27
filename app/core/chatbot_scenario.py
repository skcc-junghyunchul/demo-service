from app.core.logic import get_slot_by_rag
from app.core.logic import parse_user_id
from app.models.responses import response_generator
from app.external.ncp_redis_utils import set_conversation, get_conversation, update_conversation, delete_conversation
from app.external.openai_platform import query_openai
from app.core.chat_history_parser import chat_history_parser
from app.enums.llm_resource import LLMType
from app.models.message import Message
import json
import time
import config
from config import multi_tenant_resource
from app import logger


WELCOME_MESSAGE_PREFIX = "/welcome"
    
async def chatbot_scenario(conversation_id, company_code, user_id, user_question, message:Message):
    messages = []
 
    active_conversations = get_conversation(conversation_id)
    
    if active_conversations:
        state = active_conversations['state']
    else:
        state = None
    
    # 해결여부 확인 분기 처리
    if state == "resolution_yes_no":
        if user_question == "해결되었습니다":
            response = await response_generator(conversation_id, user_question, "대화종료", message=message)
            update_conversation(conversation_id, "finished")
            return response 
        elif user_question == "해결되지 않았습니다":           
            update_conversation(conversation_id, "awaiting_resolution")
            response = await response_generator(conversation_id, user_question, "재탐색/상담요청 여부", message=message)
            return response
        else:
            update_conversation(conversation_id, "continuing")

     # 여기이 있는 여부 확인 분기 처리           
    elif state == "awaiting_yes_no":
        if user_question == "여기에 없는 문제에요":
            response = await response_generator(conversation_id, user_question, "similar", similar_index=-1, message=message)
            update_conversation(conversation_id, "continuing")
            return response      
        else:
            update_conversation(conversation_id, "continuing")

    # 재탐색 / 상담요청 여부 확인 분기 처리
    elif state == "awaiting_resolution":
        if user_question.startswith("/상담신청완료"):
            response = "상담신청완료"
            update_conversation(conversation_id, "consultation_requested")
            return response
        elif user_question == "재탐색":
            response = await response_generator(conversation_id, user_question, "similar", similar_index=-2, message=message)  # 결과를 변수에 저장
            history = active_conversations['history']
            update_conversation(conversation_id, state="continuing")
            return response
        else:
            update_conversation(conversation_id, "continuing")

    # 상담신청 요청 확인 분기 처리
    elif state == "awaiting_consultation":
        if user_question.startswith("/상담신청완료"):
            response = "상담신청완료"
            update_conversation(conversation_id, "consultation_requested")
            return response       
        else:
            update_conversation(conversation_id, "continuing")



    
    # 첫 /welcome 질문 처리 및 company_code, user_id 파싱
    elif user_question.startswith(WELCOME_MESSAGE_PREFIX):
        user_id = parse_user_id(user_question)
        # logger.info(user_id,extra={"tenant":company_code})
        response = []
        return response

    # /상담신청완료 질문 처리
    elif user_question.startswith("/상담신청완료"):
        response = "상담신청완료"
        update_conversation(conversation_id, "consultation_requested")
        return response
    
    # multi-tenant redis에 회사코드 넣어서 회사별 openai endpoint 받아오는 로직
    if company_code in LLMType.__members__:
        resource_name = LLMType[company_code].value
    else:
        raise ValueError(f"Invalid company_code: {company_code}")
    
    # llm_resource_value = get_multi_resource(resource_name)
    llm_resource_value = multi_tenant_resource.get(resource_name)
    if not llm_resource_value:
        raise ValueError(f"LLM resource not found for company_code: {company_code}")
    # logger.info(f"llm_resource_value: {llm_resource_value}",extra={"tenant":company_code})
    
    
    ## Chichat Intent (Intent 분류 LLM 사용)
    chitchat_start = time.time()
    intent_result = await query_openai(user_question, llm_resource_value, company_code, message)
    logger.info(f"intent 분류 결과: {intent_result}",extra={"tenant":company_code})
    chitchat_end = time.time()
    logger.info(f"chitchat 분류 소요 시간: {chitchat_end - chitchat_start:.6f}초",extra={"tenant":company_code})


    if "chitchat" in intent_result:
        #chitchat으로 분류될때는 LLM 안태우고 바로 답변 나오게 하기
        if active_conversations:
            update_conversation(conversation_id, history=active_conversations['history'])
        else:
            update_conversation(conversation_id)
        return await response_generator(conversation_id, user_question, "chitchat", company_code=company_code, message=message)
    
    else:
    
        # RAG 호출        
        rag_start = time.time()
        if active_conversations:
            rag_chat_history = chat_history_parser(active_conversations['history'], company_code)
            rag_result =  await get_slot_by_rag(user_question, category=None, is_clear=None, chat_history=rag_chat_history, company_code=company_code, user_id=user_id, message=message)
            
            if "error" in rag_result:
                return await response_generator(conversation_id, user_question, "rag_error", company_code=company_code, message=message)
            
        else:
            rag_result =  await get_slot_by_rag(user_question, category=None, is_clear=None, company_code=company_code, user_id=user_id, message=message)
            if "error" in rag_result:
                return await response_generator(conversation_id, user_question, "rag_error", company_code=company_code, message=message)
        
        rag_end = time.time()
        logger.info(f"rag 소요 시간: {rag_end - rag_start:.6f}초",extra={"tenant":company_code})
        # logger.info("rag_result",extra={"tenant":company_code})
        # logger.info(rag_result,extra={"tenant":company_code})

        
    if isinstance(rag_result, dict):  # 안전한 접근
        answer_type = rag_result.get("answer_type")
        # logger.info(f"answer_type: {answer_type}",extra={"tenant":company_code})
    else:
        logger.info("Error: rag_result is not a dictionary",extra={"tenant":company_code})
        

    if answer_type == "unclear":
        
        update_conversation(conversation_id, "awaiting_yes_no")
        return await response_generator(conversation_id, user_question, answer_type, rag_result, message=message)
    
    if answer_type == "noanswer":

        update_conversation(conversation_id, "continuing")
        return await response_generator(conversation_id, user_question, answer_type, rag_result, message=message)
    
    elif answer_type == "notfound":

        update_conversation(conversation_id)
        return await response_generator(conversation_id, answer_type, rag_result, message=message)
    
    elif answer_type == "chitchat":
        return await response_generator(conversation_id, user_question, answer_type, rag_result, message=message)
    
    elif answer_type in ["forbidden", "nlu_fallback", "gpterror"]:

        update_conversation(conversation_id, "awaiting_consultation")
        return await response_generator(conversation_id, user_question, answer_type, rag_result, message=message)
        
    elif answer_type in ["text", "step"]:

        update_conversation(conversation_id, "resolution_yes_no")
        return await response_generator(conversation_id, user_question, answer_type, rag_result, message=message)
        
