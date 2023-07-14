import sys

import openai

from reliablegpt.main import reliableGPT

sys.path.append("..")


# Test 1: Basic usage
print(reliableGPT(openai.ChatCompletion.create, user_email="krrish@berri.ai"))
