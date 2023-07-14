import requests
import concurrent.futures
import time 

url = "http://0.0.0.0:4000/test_func"
params = {
  "user_email": "ipoetdawah@gmail.com",
  "instance_id": "g54b2f16-966c-4c0c-8eae-f7fdd0902a62"
}

queries = []
for i in range(200):
  query = f"who is person"
  queries.append(query)

def make_request(query):
  params["query"] = query
  params["instance_id"] = 0000
  print(f"making request{query}")
  response = requests.get(url, params=params)
  print(response)
  return response.text

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

for result in results:
  print(result)
