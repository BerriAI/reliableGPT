import sys
sys.path.append('..')

import openai
from main import reliableGPT

# Test 1: Basic usage
print(reliableGPT(openai.ChatCompletion.create, user_email="krrish@berri.ai"))

#Test 2: Rate Limit usage 
print(reliableGPT(openai.ChatCompletion.create, user_email="krrish@berri.ai", queue_requests=True))