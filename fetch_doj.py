import requests
from datetime import datetime, timezone

URL = "https://www.justice.gov/api/v1/press_releases.json"
params = {"sort": "date", "direction": "DESC"}

response = requests.get(URL, params=params, timeout=30)
response.raise_for_status()

data = response.json()
releases = data["results"]

print(f"Got {len(releases)} press releases\n")
KEYWORDS = ["aml", "bsa","money laundering", "sanctions", "bank secrecy", "fraud","fincen"]
for release in releases:
    if any(keyword in release["body"].lower() for keyword in KEYWORDS):
        date = datetime.fromtimestamp(int(release["date"]), tz=timezone.utc).date()
        print(date, "|", release["title"])
        print("    ", release["url"])