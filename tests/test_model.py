import os
import sys

import openai
from dotenv import load_dotenv
from reliablegpt.model import Model

load_dotenv()

sys.path.append("..")


openai.api_key = os.getenv("OPENAI_API_KEY")


obj = Model(openai.ChatCompletion.create)

create_completion = obj.get_original_completion()

print(create_completion(model="text-davinci-003", prompt="Hello world"))
