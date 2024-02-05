from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import Runnable
from langchain.schema.runnable.config import RunnableConfig
from modules.chat_profile import ChatProfile
import chainlit as cl
import os

# 주의사항
'''
When using LangChain, prompts and completions are not cached by default. 
To enable the cache, set the cache=true in your chainlit config file.
'''

# 실행 명령어
'''
chainlit run app.py -w (-w는 디버깅모드)
'''

# openai api key 정보 삽입
api_key = input("OpenAI API Key를 입력하세요.")
chainlit_key = input("chainlit Key를 입력하세요.")
os.environ["OPENAI_API_KEY"] = api_key
os.environ["CHAINLIT_AUTH_SECRET"] = chainlit_key


# Initialize chatprofile
chat_profiles = ChatProfile()

# Add chat profiles
@cl.set_chat_profiles
async def chat_profile():
    return [
        cl.ChatProfile(**profile) for profile in chat_profiles.get_cl_chat_profiles()
    ]

# Add password authentication with backdoor of developer names XD
@cl.password_auth_callback
def auth_callback(username: str, password: str):
    '''
        Des:
            계정 및 패스워드 입력받는 함수
        Args:
            username : ID
            password : PW
        Return:
            cl.User 또는 None
    '''
    if (username, password) == ("admin", "admin"):
        return cl.User(
            identifier="admin", 
            metadata={"role": "admin", "provider": "credentials"}
        )
    else:
        return None

@cl.on_chat_start
async def on_chat_start():
    '''
        Des:
            Chat 시작 시 수행
            - 사용자 세션을 생성함
    '''
    print("hello", cl.user_session.get("id"))
    model = ChatOpenAI(streaming=True)
    get_prompt = chat_profiles.get_system_prompt(
                            cl.user_session.get("chat_profile"))
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"You are an English teacher teaching English to Koreans.\n{get_prompt}",
            ),
            ("human", "{question}"),
        ]
    )
    runnable = prompt | model | StrOutputParser()
    cl.user_session.set("runnable", runnable)

@cl.on_chat_end
def end():
    print("goodbye", cl.user_session.get("id"))


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