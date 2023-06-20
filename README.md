# reliableGPT

Error handling Library for GPT to ensure your requests never fail. reliableGPT handles error detection and automatic retries with fallback strategies for your OpenAI calls. 

# Setup
## Step 1. pip install package
```
pip install reliableGPT
```

## Step 2. Import reliableGPT
```
from reliablegpt import reliable_create
```

## Step3. Use reliable_create as a decorator to your OpenAI call
### Code Example integrating with OpenAI
```
@reliable_create
def reliable_openai_call(model, messages, temperature):
   return openai.ChatCompletion.create(model=model,
                                            messages=messages,
                                            temperature=temperature)
```


