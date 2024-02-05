# from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import Runnable
from langchain.schema.runnable.config import RunnableConfig
import chainlit as cl
from chainlit.input_widget import Slider
import os

# 주의사항
'''
When using LangChain, prompts and completions are not cached by default. 
To enable the cache, set the cache=true in your chainlit config file.
'''

from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
model_id = "aipart/chatjob_sft_from_llama2_0.1_ALL_3epoch"
model = AutoModelForCausalLM.from_pretrained(model_id,
                                             cache_dir="../models")
tokenizer = AutoTokenizer.from_pretrained(model_id,
                                          cache_dir="../models")
    
# openai api key 정보 삽입
api_key = input("OpenAI API Key를 입력하세요.")
os.environ["OPENAI_API_KEY"] = api_key

@cl.on_chat_start
async def on_chat_start():
    '''
        Des:
            Chat 시작 시 수행
            - 사용자 세션을 생성함
    '''
    settings = await cl.ChatSettings(
        [
            Slider(id="temperature",label="temperature",initial=0.1,
                    min=0,max=1,step=0.1),
            Slider(id="top_k",label="top_k",initial=100,
                    min=0,max=200,step=10),
            Slider(id="top_p",label="top_p",initial=0.9,
                    min=0,max=1,step=0.1),
            Slider(id="max_length",label="max_length",initial=2048,
                    min=0,max=4096,step=128),
        ],
    ).send()
    
    model_kwargs={"temperature": settings["temperature"],
              "top_k":settings["top_k"],
              "top_p":settings["top_p"], 
              "max_length": settings["max_length"]}
    
    pipe = pipeline("text-generation", 
                    model=model, 
                    tokenizer=tokenizer, 
                    model_kwargs=model_kwargs, 
                    device=0)
    
    hf = HuggingFacePipeline(pipeline=pipe)
    
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                <|system|>
                당신은 직업 상담사입니다. 사용자의 질문에 대해 대답하세요.
                아래의 정보를 참고하여 사용자의 질문에 대답하세요:
                수상 이력: 2022년 DACON 문장 유형 분류 AI 경진대회 우수상
                자격증: 정보처리기사
                데이터분석전문가
                학력: 부산대학교 학사
                직업 훈련 내역: 딥러닝을 활용한 이미지 자연어처리 모델 제작 과정
                전공: 컴퓨터공학과
                근무 이력: 인턴, 한국해양과학기술원, 22.01.11 ~ 22.02.13
                """,
            ),
            ("user", "<|user|>\n{question}\n<|assistant|>"),
        ]
    )
    runnable = prompt | hf | StrOutputParser()
    cl.user_session.set("runnable", runnable)


@cl.on_message
async def on_message(message: cl.Message):
    '''
        Des:
            사용자 세션을 받아 답변 생성하는 함수
    '''
    runnable = cl.user_session.get("runnable")  # type: Runnable

    msg = cl.Message(content="") # 빈 답변 객체

    async for chunk in runnable.astream(
        {"question": message.content},
        config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()]),
    ):
        await msg.stream_token(chunk) # 모델 답변을 msg에 추가

    await msg.send() # 답변 리턴