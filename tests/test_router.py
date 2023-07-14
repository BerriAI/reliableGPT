import sys

sys.path.append("..")

import openai
from reliablegpt.main import reliableGPT

# Test 1: Basic usage
print(reliableGPT(openai.ChatCompletion.create, user_email="krrish@berri.ai"))
