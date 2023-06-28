import sys
sys.path.append('..')
import os

import dotenv
from dotenv import load_dotenv
load_dotenv()

import openai 
from Model import Model
openai.api_key = os.getenv('OPENAI_API_KEY')


obj = Model(openai.ChatCompletion.create)

create_completion = obj.get_original_completion()

print(create_completion(model="text-davinci-003", prompt="Hello world"))