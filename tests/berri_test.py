import os
import sys

import openai
from dotenv import load_dotenv

from reliablegpt.main import reliableGPT

load_dotenv()

sys.path.append("..")  # Adds the parent directory to the system path

openai.ChatCompletion.create = reliableGPT(
    openai.ChatCompletion.create,
    user_email=["ishaan@berri.ai", "krrish@berri.ai"],
    user_token="AxQgeB3aEDK2B3x4fNG3ZYJRvFfOfQuCTOR83Y_9y5g",
    queue_requests=True,
    fallback_strategy=["gpt-3.5-turbo", "text-davinci-003", "gpt-3.5-turbo"],
    model_limits_dir={"gpt-3.5-turbo": {"max_token_capacity": 40000, "max_request_capacity": 100}},
)


good_open_ai_api_key = os.getenv("OPENAI_API_KEY")

model = "gpt-3.5-turbo"
openai.api_key = good_open_ai_api_key
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Who is ishaan"},
]
temperature = 0.7

print("Making OpenAI Call")
response = openai.ChatCompletion.create(model=model, messages=messages, temperature=temperature)

print(response)
