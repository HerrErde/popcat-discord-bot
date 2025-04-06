import requests

url = "https://suggestqueries.google.com/complete/search?client=chrome&q=foobar"

response = requests.get(url)
response.raise_for_status()

if response.status_code == 200:
    data = response.json()
    first_three_results = data[1][:10]
    print(first_three_results)
else:
    print("Failed to fetch data. Status code:", response.status_code)
