from bs4 import BeautifulSoup
from templates.base import CarTemplate

class HtmlSpecTableTemplate(CarTemplate):
    name = "html_spec_table"

    def parse_car_page(self, html, car_url):
        soup = BeautifulSoup(html, "html.parser")

        car = {"url": car_url}

        for row in soup.select("table tr"):
            th = row.find("th")
            td = row.find("td")

            if th and td:
                key = th.text.strip().lower().replace(" ", "_")
                car[key] = td.text.strip()

        return car
