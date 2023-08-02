import os
import sys

import openai
from dotenv import load_dotenv
from openai.error import APIConnectionError, InvalidRequestError

from reliablegpt.model import Model

load_dotenv()

sys.path.append("..")


openai.api_key = os.getenv("OPENAI_API_KEY")


obj = Model(openai.ChatCompletion.create)

create_completion = obj.get_original_completion()

try:
    print(create_completion(model="text-davinci-003", prompt="Hello world"))
except (APIConnectionError, InvalidRequestError):
    print("API Connection Error, openai not available")
