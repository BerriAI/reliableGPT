import openai
import copy

class Model:
  """Abstraction over the OpenAI model, used to help maintain references to original functions."""

  def __init__(self, model_function):
    # Initialize instance variables
    self.model_function = model_function
    self.original_openai_chat = openai.ChatCompletion.create
    self.original_openai_completion = openai.Completion.create
    self.original_openai_embeddings = openai.Embedding.create
    self.backup_model = None


  def get_model_function(self):
    # get the model function
    return self.model_function

  def get_original_chat(self):
    return self.original_openai_chat

  def get_original_completion(self):
    return self.original_openai_completion

  def get_original_embeddings(self):
    return self.original_openai_embeddings
  
  def get_original_api_base(self):
    return self.original_api_base
  
  def get_original_api_version(self):
    return self.original_api_version
  
  def set_openai_model(self, model, api_key): # for switching from azure to openai 
    self.backup_model = model.__dict__.copy()
    model.api_type = "openai"
    model.api_base = "https://api.openai.com/v1"
    model.api_version = None
    model.api_key = api_key
    return model 

  def reset_model(self):
    return self.backup_model