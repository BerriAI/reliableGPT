import requests
import concurrent.futures
import time 
import traceback

url = "http://0.0.0.0:4000/test_func"
params = {
  "user_email": "ipoetdawah@gmail.com",
  "instance_id": "g54b2f16-966c-4c0c-8eae-f7fdd0902a62"
}

queries = []
for i in range(500):
  query = f"who is person {i+1}"
  queries.append(query)

embeddings = []
def make_request(query):
  try:
    params["query"] = query
    response = requests.get(url, params=params)
    # print("received response")
    embeddings.append(response)
    return response.text
  except:
    print(f"error occurred: {traceback.format_exc()}")

start_time = time.time()
# Use a ThreadPoolExecutor for concurrent execution
with concurrent.futures.ThreadPoolExecutor(max_workers=800) as executor:
  # Submit the requests and gather the future objects
  futures = [executor.submit(make_request, query) for query in queries]

  # Wait for all futures to complete
  concurrent.futures.wait(futures)

  # Retrieve the results
  results = [future.result() for future in futures]

# Process the results as needed

end_time = time.time() 

print(f"Total response time: {end_time - start_time}")

# for result in results:
#   print(result)
