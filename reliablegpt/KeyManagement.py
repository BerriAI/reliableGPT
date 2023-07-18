import requests
import openai

class reliableKey:
    token = "your-token-here"
    hot_cache = {}
    api_url = "https://reliable-gpt-backend-9gus.zeet-berri.zeet.app"
    valid_api_key = True

    class AuthenticationError(openai.error.AuthenticationError):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            reliableKey.set_invalid_key()

    @classmethod
    def set_invalid_key(cls):
        cls.valid_api_key = False

    @classmethod
    def get_key(cls, llm_provider, local_token=None):
        try:
            api_key = None
            if llm_provider in cls.hot_cache and cls.valid_api_key:
                api_key = cls.hot_cache[llm_provider]
            else: 
                querystring = {"llm_provider": llm_provider, "token": cls.token}
                if local_token:
                    querystring["local_token"] = local_token
                if not cls.valid_api_key:
                    querystring["invalid_api_key"] = openai.api_key
                response = requests.get(cls.api_url+"/get_key", params=querystring)
                print(response.text)
                api_key = response.json()["api_key"]
                cls.hot_cache[llm_provider] = api_key
                cls.valid_api_key = True
            return api_key
        except Exception as e:
            raise Exception("Error caused due to either a bad token or non-existent llm provider. If you're testing locally, make sure to download your .env containing your local token.")
