import asyncio
import os
import sys
sys.path.append('..')
import dotenv
from dotenv import load_dotenv
load_dotenv()

from main import reliableGPT
import openai
openai.api_key = os.getenv("AZURE_OPENAI_KEY")

## Test Azure / OpenAI Fallback 
openai.api_type = "azure"
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
openai.api_version = "2023-05-15"

print(f"openai key: {openai.api_key}")
openai.ChatCompletion.acreate = reliableGPT(
  openai.ChatCompletion.acreate, _test=True,
  user_email="krrish@berri.ai", azure_fallback_strategy=["chatgpt-v-2"], verbose=True)




async def create_chat_completion():
    chat_completion_resp = await openai.ChatCompletion.acreate(engine="chatgpt-test", model="gpt-3.5-turbo", messages=[{"role": "user", "content": "Hello world"}])
    print(chat_completion_resp)


async def call_create_chat_completion():
    for _ in range(10):
        await create_chat_completion()
        # You can add any additional code or processing here

asyncio.run(call_create_chat_completion())