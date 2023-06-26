from main import batchRequests
import openai

openai.api_key = ""

def simple_openai_call(prompt):
  print(f"in simple openai call with question:  {prompt}")
  model = "gpt-4"
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
  print(f"Result: from open ai for {prompt}, result {result}")
  return result


batch_requests = batchRequests(process_func=simple_openai_call,
                              max_token_capacity=40000,
                              max_request_capacity=200,
                              set_timeout=12000)

list_questions = [
  "What is the difference between a list and a tuple in Python?",
  "How do you iterate over a dictionary in Python?",
  "What is the purpose of the 'self' parameter in a class method?",
  "What are lambda functions in Python?",
  "How do you remove duplicates from a list in Python?",
  "What is the difference between append() and extend() methods in Python lists?",
  "How do you read a file in Python?", "How do you write to a file in Python?",
  "What is the difference between a shallow copy and a deep copy in Python?",
  "How do you convert a string to lowercase in Python?"
]

results = batch_requests.execute(list_questions)

print("\n\n\n")
print(f"Results from reliableGPT {results}")
