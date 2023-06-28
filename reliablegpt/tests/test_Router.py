import sys
sys.path.append('..')

import openai
from main import reliableGPT

print(reliableGPT(openai.ChatCompletion.create))