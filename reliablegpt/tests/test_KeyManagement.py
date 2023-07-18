import sys
sys.path.append('..')
import os
import traceback
import dotenv
from dotenv import load_dotenv
load_dotenv()

from KeyManagement import reliableKey
import openai 

## Test 1: Test with invalid openai key
openai.api_key = "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" ## Invalid OpenAI key

openai.error.AuthenticationError = reliableKey.AuthenticationError

# Test chat completion
try:
    chat_completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": "Hello world"}])
except:
    traceback.print_exc()
    pass

# Test get key
try:
    openai.api_key = reliableKey.get_key("openai")
except:
    traceback.print_exc()
    pass


## Test 2: Test with valid public token (should require a local variable in .env since this is not an allowed site_url)
reliableKey.token = "MS7JjZdDxGFpsF_QAy-JBvuqiI3LdgkJgqyr5kJmsNA"

## Test without local variable 
try:
    openai.api_key = reliableKey.get_key("openai")
except:
    traceback.print_exc()
    pass

## Test with local variable -> should succeed! 
openai.api_key = reliableKey.get_key("openai", os.getenv("KEY_LOCAL_VARIABLE"))