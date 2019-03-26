# Useful functionalities
import url, re
from urllib.parse import urlparse
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
import urllib.robotparser
from enum import Enum

# urllib implementation does only basic functionality
# It does not provide sitemap parsing
def robotsparse(url):
    rp = urllib.robotparser.RobotFileParser()
    url = canonize_url(url)

    # Parsed url
    parsedUrl = urlparse("//" + url)

    # Read url data
    uo = ""
    try:
        if parsedUrl.scheme != '':
            uo = urlopen(parsedUrl.scheme + "://" + parsedUrl.netloc + "/robots.txt").read().decode("utf-8")
        else:
            uo = urlopen("http://" + parsedUrl.netloc + "/robots.txt").read().decode("utf-8")
            
    except (HTTPError, URLError) as e:
        print(e)
        print("robots.txt inaccessible for site:", url)
        return rp, [], None

    # Parse according data
    rp.parse(uo.splitlines())

    # Find Sitemap.xml if exists
    sitemaps = re.findall("Sitemap:\s+([A-Za-z0-9\-\.\_\~\:\/\?\#\[\]\@\!\$\&\(\)\*\+\,\;\=\%]+)", uo)
    
    # For each sitemap if for some reason hosted on multiple urls
    # Get all location urls
    locations = []
    for sitemap in sitemaps:
        sm = str(urlopen(sitemap).read())
        locs = re.findall("<loc>([^<>]+)</loc>", sm)
        locations += locs
    
    # Return sitemap
    sitemap = sitemaps[0] if len(sitemaps) > 0 else None
    return rp, locations, sitemap

# Url canonization
def canonize_url(url_string):
    url_parsed = url.URL.parse(url_string)
    url_cleaned = url_parsed.strip().defrag().deparam(['utm_source']).abspath().escape().canonical().utf8
    url_cleaned = url_cleaned.decode("utf-8")
    mtch = re.match("(?:https?:\/\/)(.*)", url_cleaned)
    if mtch is not None:
        return mtch.groups()[0]
    else:
        return url_cleaned

# Content type enum
class ContentType(Enum):
    HTML = 0,
    HEAD = 1