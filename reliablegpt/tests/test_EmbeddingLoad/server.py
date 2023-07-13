from flask import Flask
import time
import openai
import sys
import traceback
import dotenv
from dotenv import load_dotenv
load_dotenv()

sys.path.append('../..')  # Adds the parent directory to the system path
import openai
from main import reliableGPT

import os 
## Test Azure / OpenAI Fallback 
openai.api_type = "azure"
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
openai.api_version = "2023-05-15"
openai.api_key = os.getenv("AZURE_OPENAI_KEY")

def logging_fn(*args, **kwargs):
  pass

openai.Embedding.create = reliableGPT(
  openai.Embedding.create,
  user_email="krrish@berri.ai",
  backup_openai_key=os.getenv('OPENAI_API_KEY'))


app = Flask(__name__)

@app.route("/test_func")
def test_fn():
  print("received request")
  try:
    text_string = "sample text" * 200
    embeddings = openai.Embedding.create(engine="azure-embedding-model",
                                      input=text_string)['data'][0]['embedding']
    return embeddings
  except:
    traceback.print_exc()
    return "Error", 500


@app.route('/')
def index():
  return 'Hello from Flask!'


if __name__ == "__main__":
  from waitress import serve
  serve(app, host="0.0.0.0", port=4000, threads=1)
