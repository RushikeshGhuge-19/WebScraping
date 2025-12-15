import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from templates.base import CarTemplate

class JsonLdVehicleTemplate(CarTemplate):
    name = "jsonld_vehicle"

    def get_listing_urls(self, html, page_url):
        soup = BeautifulSoup(html, "html.parser")
        urls = []

        for a in soup.select("a[href*='/used']"):
            urls.append(urljoin(page_url, a["href"]))

        return urls

    def parse_car_page(self, html, car_url):
        soup = BeautifulSoup(html, "html.parser")

        car = {
            "url": car_url,
            "make": "",
            "model": "",
            "price": "",
            "description": ""
        }

        for s in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(s.string)
            except Exception:
                continue

            items = data if isinstance(data, list) else [data]
            for item in items:
                t = item.get("@type")
                if t == "Vehicle" or (isinstance(t, list) and "Vehicle" in t):
                    car["make"] = item.get("brand", {}).get("name", "")
                    car["model"] = item.get("model", "")
                    car["price"] = item.get("offers", {}).get("price", "")
                    car["description"] = item.get("description", "")

        return car
