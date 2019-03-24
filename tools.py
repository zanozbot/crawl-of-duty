# Useful functionalities
import url, re
from urllib.parse import urlparse
from urllib.request import urlopen
import urllib.robotparser

rp = urllib.robotparser.RobotFileParser()

# urllib implementation does only basic functionality
# It does not provide sitemap parsing
def robotsparse(url):
    parsedUrl = urlparse(url)
    uo = str(urlopen(parsedUrl.scheme + "://" + parsedUrl.netloc + "/robots.txt").read())
    rp.parse(uo)
    sitemaps = re.findall("Sitemap:\s+([A-Za-z0-9\-\.\_\~\:\/\?\#\[\]\@\!\$\&\(\)\*\+\,\;\=\%]+)", uo)
    locations = []
    for sitemap in sitemaps:
        sm = str(urlopen(sitemap).read())
        locs = re.findall("<loc>([^<>]+)</loc>", sm)
        locations.append(locs)
    return rp, locations

# Url canonization
def canonize_url(url_string):
    url_parsed = url.URL.parse(url_string)
    url_cleaned = url_parsed.strip().defrag().deparam(['utm_source']).abspath().escape().canonical().utf8
    return url_cleaned

# Content type enum
class ContentType(Enum):
    HTML = 0,
    HEAD = 1