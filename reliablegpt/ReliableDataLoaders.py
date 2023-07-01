from typing import Any
from functools import wraps
from langchain.document_loaders.pdf import (PyMuPDFLoader, PDFMinerLoader, PyPDFLoader, OnlinePDFLoader)
from langchain.document_loaders.csv_loader import CSVLoader
from langchain.document_loaders import UnstructuredURLLoader
import resend
from termcolor import colored
from langchain.text_splitter import RecursiveCharacterTextSplitter
import traceback
import requests
import os
from uuid import uuid4
from urllib.parse import urlparse
import nltk

def setup_nltk():
    print("calling setup nltk")
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')

setup_nltk()

pdf_modules = [
  PyMuPDFLoader, PDFMinerLoader, PyPDFLoader, OnlinePDFLoader
]

csv_modules = [
  CSVLoader
]

resend.api_key = "re_X1PBTBvD_5mJfFM98AuF2278fNAGfXVNV"

default_text_splitter = RecursiveCharacterTextSplitter(chunk_size=3000,
                                               chunk_overlap=200,
                                               length_function=len)

class reliableData:

  def __init__(self, user_emails, priority_customers=[], metadata={}, text_splitter=None) -> None:
    self.user_emails = user_emails
    self.priority_customer_list = priority_customers
    self.metadata = metadata
    self.text_splitter = text_splitter
    self.customer_email = None
    pass
  
  def set_user(self, customer_email):
    self.customer_email = customer_email
    return 
  
  def fix_malformed_url(self, url):
    # Fix escaped characters
    url = url.replace("\\/", "/")

    # Parse URL
    parsed_url = urlparse(url)

    # If scheme is missing, add it
    if not parsed_url.scheme:
        url = "http://" + url
        parsed_url = urlparse(url)

    # Check if URL is valid
    if not parsed_url.netloc:
        return None
    else:
        return url
    
  def send_alert(self, error_type, filepath=None, web_url=None, additional_args=None):
    print(colored("Sending alert", "magenta"))
    # save the file
    file_url = "" 
    if filepath:
        file_extension = os.path.splitext(filepath)[1]
        filename = str(uuid4()) + file_extension
        print(filename)
        querystring = {
        "filename": filename,
        }

        post_request = requests.post(
            url='https://reliablegpt-logging-server-7nq8.zeet-berri.zeet.app/write_file',
            params=querystring,
            files={
                'file': open(filepath, 'rb')
            },
        )
        
        # Get the response
        response = post_request.json()
        print("response: ", response)
        file_url = response["response"]
    
    html = """
        <p><strong>ReliableGPT Error:</strong></p>
        <p>A critical error occurred that ReliableGPT was unable to handle.</p>
        <p>This error has happened for {}:</p>
        <p><strong>{}</strong></p>
        """.format(self.customer_email, error_type)

    if len(file_url) > 0:
      html += """<p> Here is the <a href={}>file</a> which caused the error</p>""".format(file_url)

    if web_url and len(web_url) > 0: 
      html += """<p> Here is the url which caused the error: {}</p>""".format(web_url)

    if additional_args:
      html += """<p> Here is the additional args which got passed in: {}</p>""".format(additional_args)

    # Check if the metadata exists and modify the html string
    if self.metadata:
      html += "<p>Here's the attached metadata: <strong>{}</strong></p>".format(self.metadata)

    html += """
    <p>Suggest a way we could cover this error with reliableGPT 💪:
    <a href="https://github.com/BerriAI/reliableGPT/issues/new">Here</a></p>
    <p>Join our Discord for Support:
    <a href=" https://discord.com/invite/WXFfTeEXRh">Here</a></p>"""
    params = {
      "from": "krrish@berri.ai",
      "subject": "reliableGPT 💪: {} - Unhandled Ingestion Error ".format(self.customer_email),
      "html": html
    }

    for user_email in self.user_emails:
      params["to"] = user_email
      print(params)
      email = resend.Emails.send(params)
    return

  def exceptionHandler(self, error_description, filepath=None, web_url=None):
    pages = []
    if filepath:
        if "pdf" in filepath.lower():
            print("inside pdf filepath")
            for module in pdf_modules:
                try:
                    print(f"module: {module}")
                    loader = module(filepath)
                    print(f"loader: {loader}")
                    pages = loader.load_and_split(self.text_splitter)
                    print(f"pages: {pages}")
                    if len(pages) > 0: # it worked!
                        break
                except:
                    # traceback.print_exc()
                    pass
        elif "csv" in filepath.lower():
            for module in csv_modules:
                try:
                    loader = module(filepath)
                    pages = loader.load_and_split(self.text_splitter)
                    if len(pages) > 0: # it worked!
                        break
                except:
                    pass
    elif web_url:
       url = self.fix_malformed_url(web_url)
       print("url: ", url)
       try:
        loader = UnstructuredURLLoader(urls=[url])
        pages = loader.load_and_split(self.text_splitter)
       except: 
        traceback.print_exc()
        pass
          
    if len(pages) == 0 and self.customer_email in self.priority_customer_list:
      if filepath:
        self.send_alert(error_type=error_description, filepath=filepath)
      elif web_url:
        self.send_alert(error_type=error_description, web_url=web_url)
      else:
        self.send_alert(error_type=error_description)
    return pages
