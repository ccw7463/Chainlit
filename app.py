from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import Runnable
from langchain.schema.runnable.config import RunnableConfig
import chainlit as cl
import os

# 주의사항
'''
When using LangChain, prompts and completions are not cached by default. 
To enable the cache, set the cache=true in your chainlit config file.
'''

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
    model = ChatOpenAI(streaming=True)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an English teacher teaching English to Koreans.",
            ),
            ("human", "{question}"),
        ]
    )
    runnable = prompt | model | StrOutputParser()
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