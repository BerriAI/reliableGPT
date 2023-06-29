# 💪 reliableGPT: Stop OpenAI Errors in Production 🚀

⚡️ Never worry about overloaded OpenAI servers, rotated keys, or context window limitations again!⚡️

reliableGPT handles:
* OpenAI APIError, OpenAI Timeout, OpenAI Rate Limit Errors, OpenAI Service UnavailableError / Overloaded
* Context Window Errors
* Invalid API Key errors 

## 👉 Code Examples
* [reliableGPT Getting Started](https://colab.research.google.com/drive/1za1eU6EXLlW4UjHy_YYSc7veDeGTvLON?usp=sharing)
* [reliableGPT (Advanced) OpenAI Key Manager](https://colab.research.google.com/drive/1xW-fTKjIQyVvhPLo5MWFCY7YlaMxBy_v?usp=sharing)
* 🚨**NEW** [reliableGPT + GPT-4 Rate Limit Errors](https://colab.research.google.com/drive/1zFmhRbH46Blh7U1ymPSxUcstpMgT4ETX?usp=sharing)

![ezgif com-optimize](https://github.com/BerriAI/reliableGPT/assets/17561003/017046b0-0044-4df3-a740-d5edd9e23738)

### How does it handle failures?
* **Specify a fallback strategy for handling failed requests**: For instance, you can define `fallback_strategy=['gpt-3.5-turbo', 'gpt-4', 'gpt-3.5-turbo-16k', 'text-davinci-003']`, and if you hit an error then reliableGPT will retry with the specified models in the given order until it receives a valid response. This is optional, and reliableGPT also has a default strategy it uses. 

* **Specify backup tokens**:
Using your OpenAI keys across multiple servers - and just got one rotated? You can pass backup keys using `add_keys()`. We will store and go through these, in case any get keys get rotated by OpenAI. For security, we use special tokens, and enable you to delete all your keys (using `delete_keys()`) as well. 

* **Context Window Errors**: 
For context window errors it automatically retries your request with models with larger context windows

* **Rate Limit Errors**: 
Set `queue_requests=True` and We put your requests in a queue, and run parallel batches - while accounting for your OpenAI or Azure OpenAI request + token limits (works with Langchain/LlamaIndex/Azure as well).

# Getting Started
## Step 1. pip install package
```
pip install reliableGPT
```
## Step 2. The core package is 1 line of code
Integrating with OpenAI, Azure OpenAI, Langchain, LlamaIndex
```python
from reliablegpt import reliableGPT
openai.ChatCompletion.create = reliableGPT(openai.ChatCompletion.create, user_email='ishaan@berri.ai')
```

## Advanced Usage - Queue Requests for Token & Request Limits 
### Guaranteed responses from Azure + OpenAI GPT-4, GPT 3.5 Turbo - Handle Rate Limit Errors
Use `queue_requests=True` and set your token limits as ` model_limits_dir = {"gpt-3.5-turbo": {"max_token_capacity": 1000000, "max_request_capacity": 10000}` You can find your account rate limits here: https://platform.openai.com/account/rate-limits

Here's an example request using queing to handle rate limits  
```python
openai.ChatCompletion.create = reliableGPT(
  openai.ChatCompletion.create, 
  user_email= ["ishaan@berri.ai", "krrish@berri.ai"], 
  queue_requests=True,
  model_limits_dir = {"gpt-3.5-turbo": {"max_token_capacity": 1000000, "max_request_capacity": 10000}},
  fallback_strategy=['gpt-3.5-turbo', 'text-davinci-003', 'gpt-3.5-turbo']
)
```

[👋 Give us feedback on how we could make this easier - Email us (krrish@berri.ai) or Text/Whatsapp us (+17708783106)].

### Breakdown of params
Here's everything you can pass to reliableGPT 

| Parameter | Type | Required/Optional | Description |
| --------- | ---- | ----------------- | ----------- |
| `openai.ChatCompletion.create`| OpenAI method| Required | This is a method from OpenAI, used for calling the OpenAI chat endpoints|
| `user_email`| string/list | Required | Update you on spikes in errors. You can either set user_email to one email (as user_email = "ishaan@berri.ai") or multiple (as user_email = ["ishaan@berri.ai", "krrish@berri.ai"] if you want to send alerts to multiple emails |
| `fallback_strategy` | list | Optional | You can define a custom fallback strategy of OpenAI models you want to try using. If you want to try one model several times, then just repeat that e.g. ['gpt-4', 'gpt-4', 'gpt-3.5-turbo'] will try gpt-4 twice before trying gpt-3.5-turbo | 
| `queue_requests`| bool | Optional | Set to True if you want to handle rate limit errors using a request queuing mechanism |
| `model_limits_dir`| dict | Optional | Note: Required if using `queue_requests = True`, For models you want to handle rate limits for set model_limits_dir = {"gpt-3.5-turbo": {"max_token_capacity": 1000000, "max_request_capacity": 10000}} You can find your account rate limits here: https://platform.openai.com/account/rate-limits |
| `user_token`| string | Optional | Pass your user token if you want us to handle OpenAI Invalid Key Errors - we'll rotate through your stored keys (more on this below 👇) till we get one that works|

## Handle **rotated keys** 
### Step 1. Add your keys 
```python
from reliablegpt import add_keys, delete_keys, reliableGPT
# Storing your keys 🔒
user_email = "krrish@berri.ai" # 👈 Replace with your email
token = add_keys(user_email, ["openai_key_1", "openai_key_2", "openai_key_3"])
```
Pass in a list of your openai keys. We will store these and go through them in case any get keys get rotated by OpenAI. You will get a **special token**, give that to reliableGPT.
### Step 2. Initialize reliableGPT 
```python
import openai 
openai.api_key = "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" ## Invalid OpenAI key

print("Initializing reliableGPT 💪")
openai.ChatCompletion.create = reliableGPT(openai.ChatCompletion.create, user_email= user_email, user_token = token)
```
reliableGPT💪 catches the Invalid API Key error thrown by OpenAI and rotates through the remaining keys to ensure you have **zero downtime** in production. 

### Step 3. Delete keys 
```python
#Deleting your keys from reliableGPT 🫡
delete_keys(user_email = user_email, user_token=token)
```

You own your keys, and can delete them whenever you want. 

## Support 
Reach out to us on [Discord](https://discord.gg/WXFfTeEXRh) or Email us at ishaan@berri.ai & krrish@berri.ai

