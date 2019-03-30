# Useful functionalities
import re, sys
from selenium.webdriver.chrome.options import Options
import urllib.robotparser
from urllib.parse import urlparse, unquote
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from enum import Enum    
import w3lib.url

# Drivers linux/windows/osx
platform_driver = ''
if sys.platform.startswith('linux'):
    platform_driver = './platform_dependent/linux_chromedriver'
elif sys.platform.startswith('win') or sys.platform.startswith('cygwin'):
    platform_driver = './platform_dependent/win_chromedriver.exe'
elif sys.platform.startswith('darwin'):
    platform_driver = './platform_dependent/osx_chromedriver'

# Chrome execute arguments
chrome_options = Options()
#chrome_options.add_argument("--headless")

# Get datatype from header
def get_datatype_from_header(header):
    ctype = header["Content-Type"]
    mtch = re.search("(?:application\/).*(presentationml\.presentation|-powerpoint|pdf|wordprocessingml\.document|msword)", ctype);
    if mtch is not None:
        if mtch.group(0).endswith('presentationml.presentation'):
            return "PPT"
        elif mtch.group(0).endswith('-powerpoint'):
            return "PPTX"
        elif mtch.group(0).endswith('pdf'):
            return "PDF"
        elif mtch.group(0).endswith('-powerpoint'):
            return "PPTX"
        elif mtch.group(0).endswith('wordprocessingml.document'):
            return "DOCX"
        elif mtch.group(0).endswith('msword'):
            return "DOC"

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
    parsedUrl = urlparse(url)
    return canonize_url(parsedUrl.netloc)

# urllib implementation does only basic functionality
# It does not provide sitemap parsing
def robotsparse(url):
    rp = urllib.robotparser.RobotFileParser()
    url = canonize_url(url)

    # Parsed url
    parsedUrl = urlparse(url)

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
def canonize_url(url_string, domain_url=None):
    url_cleaned = w3lib.url.canonicalize_url(url_string)
    parsed_url = urlparse(url_cleaned)
    if domain_url is not None and parsed_url.netloc == '':
        if parsed_url.path.startswith('/'):
            url_cleaned = get_domain(domain_url) + url_cleaned
        else:
            url_cleaned = get_domain(domain_url) + '/' + url_cleaned
    mtch = re.match("(?:https?:\/\/)(.*)", url_cleaned)
    if mtch is not None:
        return "http://"+mtch.groups()[0]
    else:
        return "http://"+url_cleaned

# Content type enum
class ContentType(Enum):
    HTML = 0,
    HEAD = 1