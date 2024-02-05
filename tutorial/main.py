from typing import Dict, Optional
import chainlit as cl

from langchain.embeddings import HuggingFaceEmbeddings
from transformers import AutoTokenizer
from chainlit.server import app
from fastapi import Request
from modules.chat_profile import ChatProfile
from modules.async_client import AsyncClient
from modules.conversation_chain import ConversationChain
from fastapi.responses import (
    HTMLResponse,
)

# Initialize tokenizer
tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-v0.1")

# Initialize embeddings
embedding = HuggingFaceEmbeddings()

# Initialize client
client = AsyncClient(url="http://10.0.5.187:46544")

# Initialize chatprofile
chat_profiles = ChatProfile()

# Check string token length
def check_token_length(text):
    tokens = tokenizer.tokenize(text)
    return len(tokens)


# Dummy API
@app.get("/hello")
def hello(request: Request):
    print(request.headers)
    return HTMLResponse("Hello World Test")


# Add chat profiles
@cl.set_chat_profiles
async def chat_profile():
    return [
        cl.ChatProfile(**profile) for profile in chat_profiles.get_cl_chat_profiles()
    ]


# Add password authentication with backdoor of developer names XD
@cl.password_auth_callback
def auth_callback(username: str, password: str):
    # Fetch the user matching username from your database
    # and compare the hashed password with the value stored in the database
    if (username, password) == ("admin", "admin"):
        return cl.User(
            identifier="admin", metadata={"role": "admin", "provider": "credentials"}
        )
    else:
        return None


# Add OAuth authentication
@cl.oauth_callback
def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: Dict[str, str],
    default_app_user: cl.User,
) -> Optional[cl.User]:
    return default_app_user


# TODO: on_chat_resume
# @cl.on_chat_resume
# async def on_chat_resume(conversation: ConversationDict):


@cl.on_chat_start
async def start_chat():
    print("hello", cl.user_session.get("id"))

    cl.user_session.set(
        "chain",
        ConversationChain(
            client=client,
            embedding_model=embedding,
            system_prompt=chat_profiles.get_system_prompt(
                cl.user_session.get("chat_profile")
            ),
        ),
    )


@cl.on_chat_end
def end():
    print("goodbye", cl.user_session.get("id"))


@cl.on_message  # this function will be called every time a user inputs a message in the UI
async def main(message: cl.Message):
    # Get the conversation chain from the user session.
    chain: ConversationChain = cl.user_session.get("chain")

    # Show the system prompt for the first message.
    if len(chain.conversation_history) == 1:
        await cl.Message(
            author="Setting System Prompt",
            content=f"System prompt is now successfully set to:\n`{chain.system_prompt}`",
            parent_id=message.id,
        ).send()

    # Get history from chain
    memory_dict = await chain.get_memory(message.content)

    # Show memory for long term
    if memory_dict["long_term"]:
        await cl.Message(
            author="Long-term Memory",
            content=f"Relevant long term memory :\n```\n{memory_dict['long_term']}\n```",
            parent_id=message.id,
        ).send()

    # Show memory for short term
    if memory_dict["short_term"]:
        await cl.Message(
            author="Short-term Memory",
            content=f"Previous conversation :\n```\n{memory_dict['short_term']}\n```",
            parent_id=message.id,
        ).send()

    # Get user message
    user_message = message.content

    # Get Full Prompt
    fullprompt = chain.format_prompt(
        system_prompt=chain.system_prompt,
        long_term=memory_dict["long_term"],
        short_term=memory_dict["short_term"],
        user_message=user_message,
    )

    # Show full prompt
    await cl.Message(
        author="Final Prompt",
        content=f"""Generating response for the following prompt:\n```\n{fullprompt}\n```""",
        parent_id=message.id,
    ).send()

    # Initialize bot message
    botmsg = cl.Message(content="")
    await botmsg.send()

    # Generate response from full prompt.
    async for token in chain(user_message, memory_dict):
        await botmsg.stream_token(token)

    # Append current message to conversation history.
    await chain.append_history(user_message, botmsg.content)

    # Update the vector memory.
    await botmsg.update()
