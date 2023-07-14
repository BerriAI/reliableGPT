import sys

from reliablegpt.reliable_query import reliable_query

sys.path.append("..")


@reliable_query(user_email="ishaan_test@berri.ai")
def berri_query():
    return "hi"


result = berri_query()
print(result)
