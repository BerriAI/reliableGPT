import openai


class Model:
  """Abstraction over the OpenAI model, used to help maintain references to original functions."""

  def __init__(self, model_function):
    # Initialize instance variables
    self.model_function = model_function
    self.original_openai_chat = openai.ChatCompletion.create
    self.original_openai_completion = openai.Completion.create
    self.original_openai_embeddings = openai.Embedding.create

  def get_model_function(self):
    # get the model function
    return self.model_function

  def get_original_chat(self):
    return self.original_openai_chat

  def get_original_completion(self):
    return self.original_openai_completion

  def get_original_embeddings(self):
    return self.original_openai_embeddings