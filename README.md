# reliableGPT

Error handling Library for GPT to ensure your requests never fail. reliableGPT handles error detection and automatic retries with fallback strategies for your OpenAI calls. 

This library handles:
* OpenAI APIError, OpenAI Timeout, OpenAI Rate Limit Errors, OpenAI ServiceUnavailableError / Overloaded
* Context Window Errors
  

reliableGPT simplifies openAI error handling by allowing you to specify a fallback strategy for handling failed requests. 
For instance, you can define `fallback_strategy=['gpt-3.5-turbo', 'text-davinci-003', 'text-davinci-003']`
reliableGPT monitors for errors and retries with the specified models in the given order until it receives a valid response, 
at which point it stops processing the remaining strategies.

For context window errors it automatically retries your request with models with larger context windows

# Setup
## Step 1. pip install package
```
pip install reliableGPT
```

## Step 2. Import reliableGPT
```python
from reliablegpt import reliable_create
```

## Step3. Use reliable_create as a decorator to your OpenAI call
### Code Example integrating with OpenAI
```python
from main import reliableGPT

# make openAI reliable and safe
openai.ChatCompletion.create = reliableGPT(openai.ChatCompletion.create)
```
## Support 
Reach out to us on Discord https://discord.com/invite/xqTmjKf9wC or Email us at ishaan@berri.ai & krrish@berri.ai

