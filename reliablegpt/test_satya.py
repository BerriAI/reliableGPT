import main
from main import RequestHandler, reliableGPT
import openai


def simple_openai_call(prompt, num_errors):
  #print(f"in simple openai call with question:  {prompt}")
  model = "gpt-3.5-turbo"
  messages = [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user",
      "content": prompt
    },
  ]
  result = openai.ChatCompletion.create(model=model, messages=messages)
  #print(f"Result: from open ai for {prompt}, result {result}")
  return result

list_questions = [
    "What is the difference between a list and a tuple in Python?",
    # "How do you iterate over a dictionary in Python?",
    # "What is the purpose of the 'self' parameter in a class method?",
    # "What are lambda functions in Python?",
    # "How do you remove duplicates from a list in Python?",
    # "What is the difference between append() and extend() methods in Python lists?",
    # "How do you read a file in Python?",
    # "How do you write to a file in Python?",
    # "What is the difference between a shallow copy and a deep copy in Python?",
    # "How do you convert a string to lowercase in Python?",
    # "What is the difference between a set and a frozenset in Python?",
    # "How do you handle exceptions in Python?",
    # "What is the use of the 'pass' statement in Python?",
    # "How do you reverse a string in Python?",
    # "What is the purpose of the 'if __name__ == '__main__':' statement in Python?",
    # "How do you find the length of a list in Python?",
    # "What is the difference between '==' and 'is' operators in Python?",
    # "How do you sort a dictionary by value in Python?",
    # "What is the purpose of the 'super()' function in Python?",
    # "How do you format strings in Python using f-strings?"
]

# TEST 1
# using normal request handlers 
# request_handler = RequestHandler(process_func=simple_openai_call,
#                               max_token_capacity=40000,
#                               max_request_capacity=200,
#                               verbose=True)
# for question in list_questions:
#   print("Making request")
#   print(question)
#   # async 
#   result = request_handler.execute(question)
#   print("response")
#   print(result)


# Test 2
# Using Openai wrapper
# test without package 
# Test without package
import time
import threading

def make_openai_call(question, num_errors):
    try:
        result = simple_openai_call(question, num_errors)
        print("Response:")
        print(result)
    except Exception as e:
        num_errors+=1
        print("Error:", str(e))

# # Test without package
# total_response_time = 0
num_requests = len(list_questions)
# num_errors = 0
# threads = []

# start_time = time.time()
# for question in list_questions:
#     print("Making request")
#     print(question)

#     thread = threading.Thread(target=make_openai_call, args=(question,num_errors,))
#     thread.start()
#     threads.append(thread)

# for thread in threads:
#     thread.join()

# end_time = time.time()
# total_response_time = end_time - start_time
# average_response_time = total_response_time / num_requests
# print("Average response time without package:", average_response_time, "seconds")
# print("Total response time without package:", total_response_time, "seconds")
# print("Number of error responses without package:", num_errors)

# Test with package

# print(openai.Completion.create.queue)
# print(openai.Completion.create.request_handler)
# print(openai.Completion.create.request_handler.process_func)

openai.ChatCompletion.create = reliableGPT(openai.Completion.create, user_email="ishaan@berri.ai", max_request_capacity=10000, max_token_capacity=1000000)

result = make_openai_call("who are u", 0)
print(result)
# total_response_time = 0
# num_errors = 0
# threads = []

# start_time = time.time()
# print(list_questions)
# for question in list_questions:
#     print("Making request")
#     print(question)
#     thread = threading.Thread(target=make_openai_call, args=(question, num_errors,))
#     thread.start()
#     threads.append(thread)

# for thread in threads:
#     thread.join()

# end_time = time.time()
# total_response_time = end_time - start_time
# average_response_time = total_response_time / num_requests
# print("Average response time with package:", average_response_time, "seconds")
# print("Total response time with package:", total_response_time, "seconds")
# print("Number of error responses with package:", num_errors)