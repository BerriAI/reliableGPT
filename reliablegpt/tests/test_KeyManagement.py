import sys
sys.path.append('..')
import os
import traceback
import dotenv
from dotenv import load_dotenv
load_dotenv()

from KeyManagement import reliableKey
import openai 

## Test: Test with valid public token (should require a local variable in .env since this is not an allowed site_url)
reliableKey.token = "MS7JjZdDxGFpsF_QAy-JBvuqiI3LdgkJgqyr5kJmsNA"

openai.api_key = reliableKey.get_key("openai", os.getenv("KEY_LOCAL_VARIABLE"))

openai.error.AuthenticationError = reliableKey.AuthenticationError

questions = ["Who do you know?", "What do you know?"]

for question in questions:
    try:
        chat_completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": question}])
        print(chat_completion)
    except:
        traceback.print_exc()
        continue
