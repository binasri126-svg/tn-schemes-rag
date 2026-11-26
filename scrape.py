import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
import time

url = "https://www.tn.gov.in/scheme_list.php?dep_id=Mg=="

response = requests.get(url, timeout=30)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

scheme_links = {}

# Collect all scheme links
for link in soup.find_all("a", href=True):
    href = link["href"]

    if "scheme_details.php?id=" in href:
        name = link.get_text(" ", strip=True)
        full_url = urljoin(url, href)
        scheme_links[full_url] = name

print("Total schemes found:", len(scheme_links))

schemes = []

# Extract details from each scheme
for scheme_url, name in scheme_links.items():

    try:
        response = requests.get(scheme_url, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(separator="\n", strip=True)

        # Remove unnecessary website content
        start = text.find("Concerned Department:")
        end = text.find("Content owned and Maintained by:")

        if start == -1 or end == -1 or end <= start:
            print("Skipped - details not found:", name)
            continue

        text = text[start:end].strip()

        schemes.append({
            "scheme_name": name,
            "source": scheme_url,
            "details": text
        })

        print("Extracted:", name)

    except requests.RequestException as error:
        print("Error:", name, error)

    time.sleep(1)

# Save the extracted information
with open("schemes.json", "w", encoding="utf-8") as file:
    json.dump(schemes, file, indent=4, ensure_ascii=False)

print("\nExtraction completed!")
print("Total schemes saved:", len(schemes))
print("Data saved in schemes.json")
