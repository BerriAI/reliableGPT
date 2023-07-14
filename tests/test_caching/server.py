import os
import sys
import traceback

import openai
from dotenv import load_dotenv
from flask import Flask
from reliablegpt.main import reliableGPT

load_dotenv()

sys.path.append("../..")  # Adds the parent directory to the system path


openai.api_key = os.getenv("OPENAI_API_KEY")


def logging_fn(*args, **kwargs):
    pass


openai.ChatCompletion.create = reliableGPT(
    openai.ChatCompletion.create,
    caching=True,
    user_email=["ishaan@berri.ai"],
    max_threads=1,
    verbose=True,
)


app = Flask(__name__)


@app.route("/test_func")
def test_fn():
    print("received request")
    try:
        result = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=[{"role": "user", "content": "Hello world"}]
        )
        print(f"ENDPOINT RETURNED RESULT: {result}")
        return result
    except BaseException:
        traceback.print_exc()
        return "Error", 500


@app.route("/")
def index():
    return "Hello from Flask!"


if __name__ == "__main__":
    from waitress import serve

    serve(app, host="0.0.0.0", port=4000, threads=1)
