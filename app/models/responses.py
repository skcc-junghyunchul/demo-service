import json
from app.models.rag_result import RagResult
from app.external.ncp_redis_utils import set_conversation, get_conversation, update_conversation, delete_conversation
from app.enums.chit_chat_resource import ChitChatType
from app.api.v1.multi_resource import set_multi_resource, get_multi_resource, update_multi_resource, delete_multi_resource
from app import logger
from app.models.message import Message
import config
from config import multi_tenant_resource

async def response_generator(conversation_id, user_question, response_type, rag_result: RagResult=None, similar_index: int | None=None, company_code=None, message:Message=None) -> str:
    
    if isinstance(rag_result, dict):
        rag_result = RagResult(**rag_result)
    

        
    # 공통적으로 포함될 기본 템플릿
    template = {
        "entities": [],
        "intent": [],
        "intent_ranking": [],
        "text": f"{user_question}",
    }

    # response_type에 따라 필요한 값만 추가
    if response_type in ["text", "step"]:
        template.update({
                "responses": [{

                "conversation_id": f"{conversation_id}",
                "aip_transaction_id": "" if not message.aip_transaction_id else f"{message.aip_transaction_id}",
                "text": f"문의하신 '{rag_result.user_query}'에 대해 안내드리겠습니다.",
                "image": None,
                "buttons": None,
                "custom": None
                },
            {
                "conversation_id": f"{conversation_id}",
                "aip_transaction_id": "" if not message.aip_transaction_id else f"{message.aip_transaction_id}",
                "text": None,
                "image": None,
                "buttons": None,
                "custom": {
                    "data": {
                        "answer": f"{rag_result.answer}",
                        "answer_type": f"{rag_result.answer_type}",
                        "image_paths": "" if not rag_result.image_paths else f"{rag_result.image_paths}",
                        "document_path": f"{rag_result.document_path}",
                        "doc_page_num": f"{rag_result.doc_page_num}",
                        "detail_manual_urls": "" if not rag_result.detail_manual_urls else f"{rag_result.detail_manual_urls}",
                        "similar_questions": "" if not rag_result.similar_questions else f"{rag_result.similar_questions}", 
                        "expected_questions": "" if not rag_result.expected_questions else f"{rag_result.expected_questions}",
                        "document_id": f"{rag_result.document_id}",
                        "doc_qna_num": f"{rag_result.doc_qna_num}",
                        "top_doc_question": "" if not rag_result.retrieved_document['doc_question'] else f"{rag_result.retrieved_document['doc_question']}",
                        "top_doc_answer": "" if not rag_result.retrieved_document['doc_answer'] else f"{rag_result.retrieved_document['doc_answer']}",
                        "top_doc_reranker_score": "" if not rag_result.rag_result['reranker_score'] else f"{rag_result.rag_result['reranker_score']}",
                        "sf_ticket_category_id": f"{rag_result.sf_ticket_category_id}",
                        # "rag_result": f"{rag_result.rag_result}",
                        "buttons": [
                            {"title": "해결되지 않았습니다", "payload": "해결되지 않았습니다"},
                            {"title": "해결되었습니다", "payload": "해결되었습니다"}
                        ]
                    }
                }
            }
        ]})

    elif response_type == "unclear":
        template.update({
                "responses": [{

                "conversation_id": f"{conversation_id}",
                "aip_transaction_id": "" if not message.aip_transaction_id else f"{message.aip_transaction_id}",
                "text": "정확한 답변을 드리기 위해 아래에서 문의하신 내용과 가장 적합한 증상을 선택해주세요."
                },
            {
                "conversation_id": f"{conversation_id}",
                "aip_transaction_id": "" if not message.aip_transaction_id else f"{message.aip_transaction_id}",
                "text": "",
                "custom": {
                    "data": {
                        "answer_type": "screen",
                        # "complex_questions": f"{rag_result.complex_questions}",
                        "similar_questions": "" if not rag_result.complex_questions else f"{rag_result.complex_questions}",
                        "top_doc_reranker_score": "" if not rag_result.rag_result['reranker_score'] else f"{rag_result.rag_result['reranker_score']}", 
                        # "rag_result": f"{rag_result.rag_result}",
                        "buttons": [
                            {"title": "여기에 없는 문제에요", "payload": "여기에 없는 문제에요"}
                        ]
                    }
                }
            }
        ]})

    elif response_type == "noanswer":
        # template.update({
        #     "text": "정확한 답변을 드리기 위해 아래에서 문의하신 내용과 가장 적합한 증상을 선택해주세요.",
        #     "custom": {
        #         "data": {
        #             "answer_type": "screen",
        #             "similar_questions": f"{rag_result.similar_questions}",
        #             # "rag_result": f"{rag_result.rag_result}",
        #             "buttons": [
        #                 {"title": "여기에 없는 문제에요", "payload": "여기에 없는 문제에요"}
        #             ]
        #         }
        #     }
        # })
        template.update({
                    "responses": [{

                    "conversation_id": f"{conversation_id}",
                    "aip_transaction_id": "" if not message.aip_transaction_id else f"{message.aip_transaction_id}",
                    "text": "죄송합니다, 등록된 정보에서는 요청에 대한 답변을 제공할 수 없습니다. 다른 질문이 있으시면 도와드리겠습니다."
                        },
                    {
                    "conversation_id": f"{conversation_id}",
                    "aip_transaction_id": "" if not message.aip_transaction_id else f"{message.aip_transaction_id}",
                    "text": "",
                    "custom": {
                        "data": {
                            "answer_type": f"{rag_result.answer_type}",
                            "similar_questions": "" if not rag_result.similar_questions else f"{rag_result.similar_questions}",
                            "top_doc_question": "" if not rag_result.retrieved_document['doc_question'] else f"{rag_result.retrieved_document['doc_question']}",
                            "top_doc_answer": "" if not rag_result.retrieved_document['doc_answer'] else f"{rag_result.retrieved_document['doc_answer']}",
                            "top_doc_reranker_score": "" if not rag_result.rag_result['reranker_score'] else f"{rag_result.rag_result['reranker_score']}",
                            # "rag_result": f"{rag_result.rag_result}",
                            "buttons": [
                                {"title": "IT문의", "payload": "/상담신청완료"},
                                {"title": "에이닷 문의", "payload": "A.Biz 상담"}
                                ]
                            }
                        }
                    }
                ]})
                
        
    elif response_type == "chitchat":
        
        # Validate and retrieve resource name
        if company_code not in ChitChatType.__members__:
            raise ValueError(f"Invalid company_code: {company_code}")
        
        resource_name = ChitChatType[company_code].value
        # llm_resource_value = get_multi_resource(resource_name)
        llm_resource_value = multi_tenant_resource[resource_name]
        chitchat_response_dict = json.loads(llm_resource_value['resource_value'])
        
        # logger.info(f"chit_chat_response: {chitchat_response_dict}", extra={"tenant":company_code})
        
        template.update({
                    "responses": [{

                    "conversation_id": f"{conversation_id}",
                    "aip_transaction_id": "" if not message.aip_transaction_id else f"{message.aip_transaction_id}",
                    # "text": "IT Helpdesk Online ISAC은 사내 IT 관련 문의/요청에 대한 답변, ServiceFLOW 요청서 작성, 상담신청, 내 요청 처리현황 안내, 장애 공지 안내 등을 할 수 있어요."
                    "text": "AI Helpdesk는 사내 IT 관련 문의/요청은 물론, A.Biz에 대한 문의도 가능하며, 상담 신청, 내 요청 처리현황 안내, 장애 공지 안내 등 다양한 기능을 제공해요"

                    },

                {
                    "conversation_id": f"{conversation_id}",
                    "aip_transaction_id": "" if not message.aip_transaction_id else f"{message.aip_transaction_id}",
                    "text": "",
                    "custom": {
                        "data": {
                            "answer_type":"chitchat",
                            # "rag_result": f"{rag_result.rag_result}",
                            "example": chitchat_response_dict
                        }
                    }
                }
            ]})
        
            # {
            #     "myDesk":[
            #         "파트너 사용자의 myDesk 신청을 어떻게 되나요?",
            #         "myDesk 가상 디스크 용량이 부족합니다.",
            #         "myDesk 접속이 안되요",
            #         "myDesk에서 Swing 접속 방법을 안내해 주세요"
            #     ],
            #     "Network":[
            #         "방문객 인터넷(무선랜) 접속 가능합니까?",
            #         "방문자 인터넷 사용 신청(무선랜) 신청 후 T-GUEST 로그인 실패 등 연결 오류가 발생했어요.",
            #         "네트워크 사용 불가한 상태입니다.",
            #         "모바일 단말에서 T-WNAP 무선랜 연결 설정 문의드립니다."
            #     ],
            #     "Tnet":[
            #         "T net 메뉴 추가( 메뉴 변경, 메뉴 삭제 ) 를 하고 싶어요",
            #         "T net 배너 신청을 하고 싶어요",
            #         "사내114 사진 변경은 어디서 하나요 ?",
            #         "DIY 리서치 설문 항목을 어떻게 생성해야 하나요 ?"
            #     ],
            #     "FIDO2":[
            #         "FIDO2 등록 방법을 알려주세요",
            #         "사용중인 PC 또는 휴대폰에서 FIDO2 가 지원되나요?",
            #         "FIDO2 등록 단계에서 SMS 인증번호 수신이 안됩니다.",
            #         "FIDO2 등록 시, 휴대폰을 등록하고 싶으나 Windows Hello 화면만 발생됩니다."
            #     ]
            # }
        
    elif response_type == "notfound":
        template.update({

                    "responses": [{

                        "conversation_id": f"{conversation_id}",
                        "aip_transaction_id": "" if not message.aip_transaction_id else f"{message.aip_transaction_id}",
                        "text": f"'{rag_result.user_query}'에 대한 정확한 정보를 찾을 수 없었습니다. 유사한 증상을 찾아보세요."
                    },
                    {
                        "conversation_id": f"{conversation_id}",
                        "aip_transaction_id": "" if not message.aip_transaction_id else f"{message.aip_transaction_id}",
                        "text": "",
                        "custom": {
                            "data": {
                                "answer_type": "similar",
                                "similar_questions": "" if not rag_result.similar_questions else f"{rag_result.similar_questions}", 
                                "top_doc_question": "" if not rag_result.retrieved_document['doc_question'] else f"{rag_result.retrieved_document['doc_question']}",
                                "top_doc_answer": "" if not rag_result.retrieved_document['doc_answer'] else f"{rag_result.retrieved_document['doc_answer']}",
                                "top_doc_reranker_score": "" if not rag_result.rag_result['reranker_score'] else f"{rag_result.rag_result['reranker_score']}",
                                # "rag_result": f"{rag_result.rag_result}"
                            }
                        }
                    }
                ]})

    elif response_type == "forbidden":
        template.update({
                        "responses": [{

                        "conversation_id": f"{conversation_id}",
                        "aip_transaction_id": "" if not message.aip_transaction_id else f"{message.aip_transaction_id}",
                        "text": "문의하신 내용에 대해 아래와 같은 사유로 인해 답변을 드릴 수 없습니다."
                        },
                    {
                        "conversation_id": f"{conversation_id}",
                        "aip_transaction_id": "" if not message.aip_transaction_id else f"{message.aip_transaction_id}",
                        "text": "",
                        "custom": {
                            "data": {
                                "answer": f"{rag_result.answer}",
                                "answer_type": f"{rag_result.answer_type}",
                                "image_paths": "" if not rag_result.image_paths else f"{rag_result.image_paths}",
                                "document_path": f"{rag_result.document_path}",
                                "doc_page_num": f"{rag_result.doc_page_num}",
                                "detail_manual_urls": "" if not rag_result.detail_manual_urls else f"{rag_result.detail_manual_urls}",
                                "similar_questions": "" if not rag_result.similar_questions else f"{rag_result.similar_questions}",
                                "expected_questions": "" if not rag_result.expected_questions else f"{rag_result.expected_questions}",
                                "document_id": f"{rag_result.document_id}",
                                "doc_qna_num": f"{rag_result.doc_qna_num}",
                                "top_doc_question": "" if not rag_result.retrieved_document['doc_question'] else f"{rag_result.retrieved_document['doc_question']}",
                                "top_doc_answer": "" if not rag_result.retrieved_document['doc_answer'] else f"{rag_result.retrieved_document['doc_answer']}",
                                "top_doc_reranker_score": "" if not rag_result.rag_result['reranker_score'] else f"{rag_result.rag_result['reranker_score']}",
                                # "rag_result": f"{rag_result.rag_result}",
                                "buttons": [
                                    {"title": "IT문의", "payload": "/상담신청완료"},
                                    {"title": "에이닷 문의", "payload": "A.Biz 상담"}
                                ]
                            }
                        }
                    }
        ]})

    elif response_type == "rag_error":
        template.update({
                        "responses": [{

                        "conversation_id": f"{conversation_id}",
                        "aip_transaction_id": "" if not message.aip_transaction_id else f"{message.aip_transaction_id}",
                        "text": "시스템의 일시적인 오류로 인해 답변을 드릴 수 없습니다. 잠시 후 다시 시도해주세요."
                        },
                    {
                        "conversation_id": f"{conversation_id}",
                        "aip_transaction_id": "" if not message.aip_transaction_id else f"{message.aip_transaction_id}",
                        "aip_transaction_id": f"{message.aip_transaction_id}",
                        "text": "",
                        "custom": {
                            "data": {
                                # "answer_type": f"{rag_result.answer_type}",
                                # "similar_questions": "" if not rag_result.similar_questions else f"{rag_result.similar_questions}",
                                # "rag_result": "" if not rag_result.rag_result else f"{rag_result.rag_result}",
                                # "top_doc_question": "" if not rag_result.retrieved_document['doc_question'] else f"{rag_result.retrieved_document['doc_question']}",
                                # "top_doc_answer": "" if not rag_result.retrieved_document['doc_answer'] else f"{rag_result.retrieved_document['doc_answer']}",
                                # "top_doc_reranker_score": "" if not rag_result.rag_result['reranker_score'] else f"{rag_result.rag_result['reranker_score']}",
                                "buttons": [
                                    {"title": "IT문의", "payload": "/상담신청완료"},
                                    {"title": "에이닷 문의", "payload": "A.Biz 상담"}
                                ]
                            }
                        }
                    }
                ]})

    elif response_type == "nlu_fallback":
        template.update({
                        "responses": [{

                        "conversation_id": f"{conversation_id}",
                        "aip_transaction_id": "" if not message.aip_transaction_id else f"{message.aip_transaction_id}",
                        "text": "정확한 답변을 찾아봤는데 없네요. 전체 시스템에서 유사한 증상을 한번 찾아봤어요."
                        },
                    {
                        "conversation_id": f"{conversation_id}",
                        "aip_transaction_id": "" if not message.aip_transaction_id else f"{message.aip_transaction_id}",
                        "text": "",
                        "custom": {
                            "data": {
                                "answer_type": "nlu_fallback",
                                "teams": "정확한 답변을 찾지 못했습니다. 유사한 증상을 찾아보세요.",
                                "similar_questions": "" if not rag_result.similar_questions else f"{rag_result.similar_questions}",
                                # "rag_result": f"{rag_result.rag_result}",
                                "top_doc_question": "" if not rag_result.retrieved_document['doc_question'] else f"{rag_result.retrieved_document['doc_question']}",
                                "top_doc_answer": "" if not rag_result.retrieved_document['doc_answer'] else f"{rag_result.retrieved_document['doc_answer']}",
                                "top_doc_reranker_score": "" if not rag_result.rag_result['reranker_score'] else f"{rag_result.rag_result['reranker_score']}",
                                "buttons": [
                                    {"title": "IT문의", "payload": "/상담신청완료"},
                                    {"title": "에이닷 문의", "payload": "A.Biz 상담"}
                                ]
                            }
                        }
                    }
                ]})

    elif response_type == "재탐색/상담요청 여부":
        template.update({
                        "responses": [{

                        "conversation_id": f"{conversation_id}",
                        "aip_transaction_id": "" if not message.aip_transaction_id else f"{message.aip_transaction_id}",
                        "text": "셀프 조치를 통해 해결이 어려우셨나요? 해결하기 어려웠던 문제를 아래에 입력하시거나 '재탐색'을 선택해 유사한 문제를 확인해주세요. 겪고 있는 문제가 무엇인지 파악하기 어렵다면 'IT문의' 또는 'A.Biz문의'를 선택해 주세요.",
                        "image": None,
                        "buttons": [
                            {"title": "재탐색", "payload": "재탐색"},
                            {"title": "IT문의", "payload": "/상담신청완료"},
                            {"title": "에이닷 문의", "payload": "A.Biz 상담"}
                            ],
                        "custom": None
                        }]
                    })

    elif response_type == "대화종료":
        template.update({
                        "responses": [{

                        "conversation_id": f"{conversation_id}",
                        "aip_transaction_id": "" if not message.aip_transaction_id else f"{message.aip_transaction_id}",
                        "text": "대화창에 다른 문의 내용을 입력하시거나 아래에서 대화 종료 버튼을 선택해 대화를 종료할 수 있습니다."
                        },
                    {
                        "conversation_id": f"{conversation_id}",
                        "aip_transaction_id": "" if not message.aip_transaction_id else f"{message.aip_transaction_id}",
                        "text": "",
                        "custom": {
                            "data": {
                                "answer_type": "exit",
                                "buttons": [
                                    {"title": "대화종료", "payload": "/대화종료"}
                                ]
                            }
                        }
                    }
                ]})


    elif response_type == "similar":
        
        active_conversations = get_conversation(conversation_id)
        if active_conversations:
            if active_conversations['history'] != {}:
                memory_similar_questions = active_conversations['history'][similar_index]['agent']['responses'][1]['custom']['data']['similar_questions']
                memory_user_query = active_conversations['history'][similar_index]['user']
                
        template.update({
                        "responses": [{

                        "conversation_id": f"{conversation_id}",
                        "aip_transaction_id": "" if not message.aip_transaction_id else f"{message.aip_transaction_id}",
                        "text": f"다음은 '{memory_user_query}'와 유사한 증상이에요. 본인의 증상과 가장 유사한 내용을 아래에서 선택해주세요."
                        },
                    {
                        "conversation_id": f"{conversation_id}",
                        "aip_transaction_id": "" if not message.aip_transaction_id else f"{message.aip_transaction_id}",
                        "text": "",
                        "custom": {
                            "data": {
                                "answer_type": "similar",
                                "similar_questions": "" if not memory_similar_questions else f"{memory_similar_questions}",
                                "buttons": [
                                    {"title": "IT문의", "payload": "/상담신청완료"},
                                    {"title": "에이닷 문의", "payload": "A.Biz 상담"}
                                ]
                            }
                        }
                    }
                ]})


    return template
