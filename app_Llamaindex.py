import os
import openai

from llama_index.query_engine.retriever_query_engine import RetrieverQueryEngine
from llama_index.callbacks.base import CallbackManager
from llama_index import (
    LLMPredictor,
    ServiceContext,
    StorageContext,
    load_index_from_storage,
)
from langchain_openai import ChatOpenAI
import chainlit as cl
from loguru import logger

# openai api key 정보 삽입
api_key = input("OpenAI API Key를 입력하세요.")
os.environ["OPENAI_API_KEY"] = api_key
openai.api_key = os.environ.get("OPENAI_API_KEY")


try:
    # 벡터 스토어 들고와서 인덱스로드
    logger.info("Storage Context Rebuild")
    storage_context = StorageContext.from_defaults(persist_dir="./storage")
    logger.info("Load Index")
    index = load_index_from_storage(storage_context)
except:
    from llama_index import GPTVectorStoreIndex, SimpleDirectoryReader
    logger.info("Load Data")
    documents = SimpleDirectoryReader("./data").load_data()
    logger.info("Make Index from docs")
    index = GPTVectorStoreIndex.from_documents(documents)
    index.storage_context.persist()

print("index :",index)

@cl.on_chat_start
async def factory():
    llm_predictor = LLMPredictor(
        llm=ChatOpenAI(
            temperature=0,
            model_name="gpt-3.5-turbo",
            streaming=True,
        ),
    )
    service_context = ServiceContext.from_defaults(
        llm_predictor=llm_predictor,
        chunk_size=512,
        callback_manager=CallbackManager([cl.LlamaIndexCallbackHandler()]),
    )
    print("service_context :",service_context)
    query_engine = index.as_query_engine(
        service_context=service_context,
        streaming=True,
    )

    cl.user_session.set("query_engine", query_engine)


@cl.on_message
async def main(message: cl.Message):
    query_engine = cl.user_session.get("query_engine")  # type: RetrieverQueryEngine
    response = await cl.make_async(query_engine.query)(message.content) # 쿼리날려 얻은 정보를 포함하여 답변생성?
    response_message = cl.Message(content="")

    for token in response.response_gen:
        await response_message.stream_token(token=token)

    if response.response_txt:
        response_message.content = response.response_txt

    await response_message.send()