import sys
sys.path.append('..')

from langchain.text_splitter import RecursiveCharacterTextSplitter
from ReliableDataLoaders import reliableData

text_splitter = RecursiveCharacterTextSplitter(chunk_size=3000,
                                               chunk_overlap=200,
                                               length_function=len)

rDL = reliableData(user_emails=["krrish@berri.ai"],
                   priority_customers=["ishaan@berri.ai"], metadata={"environment": "local"}, text_splitter=text_splitter)



rDL.set_user("ishaan@berri.ai")

# Test Case 1: Malformed URLs
rDL.exceptionHandler(error_description="error", web_url="https:\\/\\/test.hosteeva.com\\/properties\\/available\\/details\\/451-peters-unit-401-test-1")

# Test Case 2: Bad PDF 
rDL.exceptionHandler(error_description="error", filepath="../../files/bad.pdf")

# Test Case 3: Good PDF 
rDL.exceptionHandler(error_description="error", filepath="../../files/good.pdf")

# Test Case 4: Bad CSV 
rDL.exceptionHandler(error_description="error", filepath="../../files/bad.csv")

# Test Case 5: Good CSV
rDL.exceptionHandler(error_description="error", filepath="../../files/good.csv")