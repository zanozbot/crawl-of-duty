from database.models import *
from urllib.parse import urlparse
import re

class Crawler:

    def __init__(self):
        print(DataType(code="PDF").code)
        print(self.normalize_url('https://www.cwi.nl:80/%7Eguido/Python/1239/index.html?id=213'))

    def normalize_url(self, url):
        parsed_url = urlparse(url)
        exploded_path = re.search("(.*\/)(.+)(\..+)", parsed_url.path)
        return parsed_url.scheme + "://" + parsed_url.hostname + exploded_path[1] + exploded_path[2]


Crawler()