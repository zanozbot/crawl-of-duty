# Useful functionalities
import url, re
import urllib.robotparser
from urllib.parse import urlparse, unquote
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from enum import Enum

# Find locations in sitemap
def get_sitemap_locations(sitemap):
    locs = re.findall("<loc>([^<>]+)</loc>", sitemap)
    locs = [canonize_url(loc) for loc in locs]
    return locs

# Get robotparser object
def get_robotparser(robotsText):
    rp = urllib.robotparser.RobotFileParser()
    
    # Parse according data
    rp.parse(robotsText.splitlines())
    
    return rp

def get_domain(url):
    url = canonize_url(url)

    # Parsed url
    parsedUrl = urlparse("//" + url)
    return parsedUrl.netloc

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
        return '', ''

    # Parse according data
    rp.parse(uo.splitlines())

    # Find Sitemap.xml if exists
    sitemaps = re.findall("Sitemap:\s+([A-Za-z0-9\-\.\_\~\:\/\?\#\[\]\@\!\$\&\(\)\*\+\,\;\=\%]+)", uo)
    
    # For each sitemap if for some reason hosted on multiple urls
    # Get all location urls
    sitemap_contents = ""
    for sitemap in sitemaps:
        sm = str(urlopen(sitemap).read())
        sitemap_contents += sm
    
    return unquote(str(rp)), sitemap_contents

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