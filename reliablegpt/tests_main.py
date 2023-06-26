import openai
from main import reliableGPT
import uuid

openai.api_key = ""
from tenacity import retry, stop_after_attempt, wait_random_exponential

# make openAI reliable and safe
openai.ChatCompletion.create = reliableGPT(openai.ChatCompletion.create, user_email= "ishaan@berri.ai", user_token = "AxQgeB3aEDK2B3x4fNG3ZYJRvFfOfQuCTOR83Y_9y5g", send_notification=True)
openai.Completion.create = reliableGPT(openai.Completion.create, user_email= "ishaan@berri.ai", user_token = "AxQgeB3aEDK2B3x4fNG3ZYJRvFfOfQuCTOR83Y_9y5g", send_notification=True)
openai.Embedding.create = reliableGPT(openai.Embedding.create, user_email= "ishaan@berri.ai", user_token = "AxQgeB3aEDK2B3x4fNG3ZYJRvFfOfQuCTOR83Y_9y5g", send_notification=True)

def open_ai_completion_call():
    model = "gpt-4"
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Who won the world series in 2020?"},
        {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
        {"role": "user", "content": "Where was it played?"}
    ]
    temperature = 0.7
    metadata = {
        "request_uuid": str(uuid.uuid4()),  # Generate a new UUID for each request
        "user": "ishaan@berri.ai"
    }
    response = openai.ChatCompletion.create(model=model, messages=messages, temperature=temperature)
    print(response)


@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
def get_embedding(text, model="text-embedding-ada-002", metadata={}):
  text = text.replace("\n", " ")
  return openai.Embedding.create(input=[text],
                                 model=model, metadata=metadata)["data"][0]["embedding"]

def open_ai_embed_call():
    # openai.Embedding.create = reliableGPT(openai.Embedding.create, user_email= "ishaan@berri.ai", user_token = 'QA5T6lYfzB-8u3gFlC0hxtBZ-TbkJRF_FwrCB8GKTLM', send_notification=True)
    text = """
    Write in less than 25 words a hyper contextualized message about your company and how what your company does could help the visiting company's product offering. Start the message with a lowercase letter.
Reference previous successful chat conversations for the tone and voice. Mix up the language. Try saying something new to each visitor. Make sure it makes sense. Be as specific as possible. If you don't know the person or the company then write a funny
joke based on the person's location. If you don't have the person's location then write a message based on the information of the page the person is on. If you know the person's company mention the person's company in the message. If you don't know the company
then don't mention it. Take into account previous chat history and context around the company and the visitor. Do not include any urls in the response.
At the very end of the message say "(not a bot btw, real person)". Speak succinctly as you would to your best friend.
Your response to the visitor on the site should be as helpful as possible. If you know the company the person works for or the person's name, include the first name or company name in the message.
If the person's name or company is not known, then start the message with "hey!" Craft the style of your message as the best sales development representative in the world would write.
Do not say the same message twice to the person. Start the response with a lowercase letter. Do not start a new conversation or message the person if you've already messaged them within 72 hours.
    """
    metadata = {
                "request_uuid": "40ae3a49-8a01-4c47-9985-6f22bca8c5b6", 
                "user": "ishaan@berri.ai"
    }
    embedding_result = get_embedding(text, metadata=metadata)
    print(embedding_result)
    return embedding_result


import concurrent.futures

def test_multiple_calls():
    model = "gpt-4"
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Who won the world series in 2020?" * 600},
        {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
        {"role": "user", "content": "Where was it played?"}
    ]
    temperature = 0.7

    error_count = 0
    failure_count = 0  # Track the number of failures

    def call_reliable_openai():
        nonlocal error_count, failure_count
        try:
            print("Making OpenAI Call")

            response = openai.ChatCompletion.create(model=model, messages=messages, temperature=temperature)
            print(response)
            if response and "error" in response:
                error_count += 1
            if response == "Sorry, the OpenAI (GPT) failed":
                failure_count += 1

        except Exception as e:
            print("Exception occurred:", e)
            error_count += 1

    # Create a ThreadPoolExecutor with a maximum of 10 threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        # Submit the callable to the executor for each call
        future_calls = [executor.submit(call_reliable_openai) for _ in range(20)]

        # Wait for all the futures to complete
        concurrent.futures.wait(future_calls)

    print(f"Error Count: {error_count}")
    print(f"Fallback response count: {failure_count}")

    if error_count == 0:
        print("All calls executed successfully.")
    else:
        print("Some calls returned errors.")




def test_single_call_bad_key():
    openai.api_key = "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"
    model = "gpt-4"
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Who won the Chess championship 2022"*100},
    ]
    temperature = 0.7

    error_count = 0
    failure_count = 0  # Track the number of failures

    try:
        print("Making OpenAI Call")
        response = openai.ChatCompletion.create(model=model, messages=messages, temperature=temperature)
        if response and "error" in response:
            error_count += 1
        if response == "Sorry, the OpenAI (GPT) failed":
            failure_count += 1
    except Exception as e:
        print("Exception occurred:", e)
        error_count += 1

    print(f"Error Count: {error_count}")
    print(f"Fallback response count: {failure_count}")

    if error_count == 0:
        print("All calls executed successfully.")
    else:
        print("Some calls returned errors.")

# test_single_call_bad_key()

def krrish_test_key():
    openai.api_key = "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" 
    completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": "Hello world"}])
    print(completion)
# krrish_test_key()
# def test_add_keys():
#     result = main.add_keys(account_email="ishaan1@berri.ai", keys=["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", "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"])
#     print(result)

# def test_delete_keys():
#     result = main.delete_keys(account_email="ishaan@berri.ai", account_token="OwfY1OFqy8fxR0zsJQPW_tcMPo8N7_vP8x3YW-dU9R8")
#     print(result)


# test_add_keys()
# test_delete_keys()


def test_embedding_bad_key():
    from main import reliableGPT
    openai.Embedding.create = reliableGPT(openai.Embedding.create, user_email= "ishaan@berri.ai", user_token = 'QA5T6lYfzB-8u3gFlC0hxtBZ-TbkJRF_FwrCB8GKTLM', send_notification=True)

    openai.api_key = "bad-key"
    def get_embedding(text, model="text-embedding-ada-002"):
        text = text.replace("\n", " ")
        print("text")
        return openai.Embedding.create(input=[text],
                                        model=model)["data"][0]["embedding"]
    result = get_embedding("GM")
    #print(f"This is the embedding response {result}")

#open_ai_completion_call()
#test_embedding_bad_key()
#open_ai_embed_call()
test_multiple_calls()