import requests

html = requests.get("https://www.anyvehicle.co.uk/used-cars", timeout=15).text
print(html[:500])
