import sys
sys.path.append('..')

import openai
from main import reliable_query

@reliable_query(user_email='ishaan_test@berri.ai')
def berri_query():
    return "hi"

result = berri_query()
print(result)
