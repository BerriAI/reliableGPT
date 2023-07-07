import requests
import concurrent.futures
import time 

url = "http://0.0.0.0:4000/test_func"

queries = []
for i in range(40):
  query = f"who is person {i+1}"
  queries.append(query)


def make_request(query):
  print(f"making request{query}")
  response = requests.get(url)
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

# for result in results:
#   print(result)
