# 💪 reliableGPT: Stop failing customer requests for your LLM App 🚀
[![](https://dcbadge.vercel.app/api/server/wuPM9dRgDw)](https://discord.gg/wuPM9dRgDw)

⚡️ Get 0 dropped requests for your LLM app in production ⚡️

When a request to your llm app fails, reliableGPT handles it by:
* Retrying with an alternate model - GPT-4, GPT3.5, GPT3.5 16k, text-davinci-003
* Retrying with a larger context window model for Context Window Errors
* Sending a Cached Response (using semantic similarity)
* Retry with a fallback API key for Invalid API Key errors 

## Community 
* Join us on [Discord](https://discord.gg/WXFfTeEXRh) or Email us at ishaan@berri.ai & krrish@berri.ai
* **Talk to Founders: Learn more / get help onboarding: [Meeting Scheduling Link](https://calendly.com/d/yr3-9zt-yy4/reliablegpt?month=2023-07)**


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

## Troubleshooting
If you experience failure, try 
```
pip install reliableGPT==0.2.976
```

## 👉 Code Examples
* [reliableGPT Getting Started](https://colab.research.google.com/drive/1za1eU6EXLlW4UjHy_YYSc7veDeGTvLON?usp=sharing)
* [reliableGPT (Advanced) OpenAI Key Manager](https://colab.research.google.com/drive/1xW-fTKjIQyVvhPLo5MWFCY7YlaMxBy_v?usp=sharing)

![ezgif com-optimize](https://github.com/BerriAI/reliableGPT/assets/17561003/017046b0-0044-4df3-a740-d5edd9e23738)

### How does it handle failures?
* **Specify a fallback strategy for handling failed requests**: For instance, you can define `fallback_strategy=['gpt-3.5-turbo', 'gpt-4', 'gpt-3.5-turbo-16k', 'text-davinci-003']`, and if you hit an error then reliableGPT will retry with the specified models in the given order until it receives a valid response. This is optional, and reliableGPT also has a default strategy it uses. 

* **Specify backup tokens**:
Using your OpenAI keys across multiple servers - and just got one rotated? You can pass backup keys using `add_keys()`. We will store and go through these, in case any get keys get rotated by OpenAI. For security, we use special tokens, and enable you to delete all your keys (using `delete_keys()`) as well. 

* **Context Window Errors**: 
For context window errors it automatically retries your request with models with larger context windows

* **Caching**
If model fallback + retries fails - reliableGPT also provides caching (hosted - not in-memory). You can turn this on with `caching=True`. This also works for request timeout / task queue depth issues. This is optional, scroll down to learn more 👇. 

## Advanced Usage
### Breakdown of params
Here's everything you can pass to reliableGPT 

| Parameter | Type | Required/Optional | Description |
| --------- | ---- | ----------------- | ----------- |
| `openai.ChatCompletion.create`| OpenAI method| Required | This is a method from OpenAI, used for calling the OpenAI chat endpoints|
| `user_email`| string/list | Required | Update you on spikes in errors. You can either set user_email to one email (as user_email = "ishaan@berri.ai") or multiple (as user_email = ["ishaan@berri.ai", "krrish@berri.ai"] if you want to send alerts to multiple emails |
| `fallback_strategy` | list | Optional | You can define a custom fallback strategy of OpenAI models you want to try using. If you want to try one model several times, then just repeat that e.g. ['gpt-4', 'gpt-4', 'gpt-3.5-turbo'] will try gpt-4 twice before trying gpt-3.5-turbo | 
| `model_limits_dir`| dict | Optional | Note: Required if using `queue_requests = True`, For models you want to handle rate limits for set model_limits_dir = {"gpt-3.5-turbo": {"max_token_capacity": 1000000, "max_request_capacity": 10000}} You can find your account rate limits here: https://platform.openai.com/account/rate-limits |
| `user_token`| string | Optional | Pass your user token if you want us to handle OpenAI Invalid Key Errors - we'll rotate through your stored keys (more on this below 👇) till we get one that works|
| `azure_fallback_strategy`| List[string] | Optional | Pass your backup azure deployment/engine id's. In case your requests start failing we'll switch to one of these (if you also pass in a backup openai key, we'll try the Azure endpoints before the raw OpenAI ones) |
| `backup_openai_key`| string | Optional | Pass your OpenAI API key if you're using Azure and want to switch to OpenAI in case your requests start failing |
| `caching` | bool | Optional | Cache your openai responses, Used as backup in case model fallback fails **or** overloaded queue (if you're servers are being overwhelmed with requests, it'll alert you and return cached responses, so that customer requests don't get dropped) | 
| `max_threads` | int | Optional | Pass this in alongside `caching=True`, for it to handle the overloaded queue scenario |

# 👨‍🔬 Use Cases

## Switch between Azure OpenAI and raw OpenAI
If you're using Azure OpenAI and facing issues like Read/Request Timeouts, Rate limits, etc. you can use reliableGPT 💪 to fall back to the raw OpenAI endpoints if your Azure OpenAI endpoint fails 
### Step 1. Import reliableGPT 
```python
from reliablegpt import reliableGPT
```

### Step 2. Set your backup openai token + [Optional] Set fallback strategy
Note: **This is stored locally.** 
```python
#Set the backup openai key
openai.ChatCompletion.create = reliableGPT(
  openai.ChatCompletion.create,
  user_email="krrish@berri.ai",
  backup_openai_key=os.getenv("OPENAI_API_KEY"),
  fallback_strategy=["gpt-4", "gpt-4-32k"],
  verbose=True)
```

### Step 3. Test with a bad Azure Key! 
```python
#bad key
openai.api_key = "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"

for question in list_questions:
  response = openai.ChatCompletion.create(model="gpt-4", engine="chatgpt-test", messages=[{"role":"user", "content": "Hey! how's it going?"}])
  print(response)
```

## Handle overloaded server w/ Caching
If all else fails, reliableGPT will respond with previously cached responses. We store this in a Supabase table and use cosine similarity for similarity based retrieval. Why not in-memory cache? Because when we autoscale / push new updates to our server, we didn't want the cache to be wiped out. 

### Step 1. Import reliableGPT 
```python
from reliablegpt import reliableGPT
```

### Step 2. Turn on caching
```python
#Set the backup openai key
openai.ChatCompletion.create = reliableGPT(
  openai.ChatCompletion.create,
  user_email="krrish@berri.ai",
  caching=True)
```

#### Optional: Pass your max threads
Tell reliableGPT what the maximum number of threads you have, handling your requests for you. 
e.g. The number of threads for this flask app is `50`
```python
if __name__ == "__main__":
  from waitress import serve
  serve(app, host="0.0.0.0", port=4000, threads=50)
```

Tell reliableGPT what the maximum number of threads is - `max_threads=50`
```python
#Set the backup openai key
openai.ChatCompletion.create = reliableGPT(
  openai.ChatCompletion.create,
  user_email="krrish@berri.ai",
  caching=True,
  max_threads=50)
```

### Step 3. Test it
Check out [./reliablegpt/tests/test_Caching](https://github.com/BerriAI/reliableGPT/tree/main/reliablegpt/tests/test_Caching)

We spin up a flask server, and then run a test script to run a set of questions against the flask server. 

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

