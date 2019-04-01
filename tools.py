# Useful functionalities
import re, sys
from selenium.webdriver.chrome.options import Options
import urllib.robotparser
from urllib.parse import urlparse, unquote
from enum import Enum    
import w3lib.url
import requests
from requests import RequestException
from time import sleep

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
chrome_options.add_argument("--headless")

# Get datatype from header
def get_mime_type_from_header(header):
    matchStr = (
        "(application\/|image\/|text\/)"
        "(json|jpeg|x-citrix-jpeg"
        "|vnd.openxmlformats-officedocument.wordprocessingml.document"
        "|vnd.ms-powerpoint"
        "|vnd.openxmlformats-officedocument.presentationml.presentation"
        "|msword"
        "|pdf|png|x-citrix-png|x-png|x-portable-graymap"
        "|gif|bmp|tiff|svg+xml|svg"
        "|webp|xml"
        "|xhtml+xml|xhtml|html)"
    )

    mimeDict = {
        "application/json" : ".json",
        "image/jpeg" : ".jpeg",
        "image/x-citrix-jpeg" : ".jpeg",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document" : ".docx",
        "application/docx" : ".docx",
        "application/msword" : ".doc",
        "application/doc" : ".doc",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation" : ".pptx",
        "application/pptx" : ".pptx",
        "application/vnd.ms-powerpoint" : ".ppt",
        "application/ppt" : ".ppt",
        "application/pdf" : ".pdf",
        "image/png" : ".png",
        "image/x-citrix-png" : ".png",
        "image/x-png" : ".png",
        "image/x-portable-graymap" : ".pgm",
        "image/pgm" : ".pgm",
        "image/gif" : ".gif",
        "image/bmp" : ".bmp",
        "image/tiff" : ".tiff",
        "image/svg+xml" : ".svg",
        "image/svg" : ".svg",
        "image/webp" : ".webp",
        "application/xhtml+xml" : ".xhtml",
        "application/xhtml" : ".xhtml",
        "text/html" : ".html",
        "text/xml" : ".xml",
        "application/xml" : ".xml"
    }

    ctype = header["Content-Type"]
    mtch = re.search(matchStr, ctype)
    if mtch is not None:
        return mimeDict[mtch.group(0)] if mtch.group(0) in mimeDict else "."+(mtch.group(0)[(mtch.group(0).index('/')+1):])
    else:
        return None

def ending_to_datatype(ending):
    if ending == ".xhtml" or ending == ".xml" or ending == ".html":
        return "HTML"
    else:
        return ending.upper()[1:]

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


# get data
def get_robots_data(url):
    url = canonize_url(url)

    # Parsed url
    parsedUrl = urlparse(url)

    # Read url data
    uo = ""

    try:
        if parsedUrl.scheme != '':
            res = requests.get(parsedUrl.scheme + "://" + parsedUrl.netloc + "/robots.txt", timeout=(5,7) )
            if res.text is not None:
                uo = res.text
            else:
                uo = ""
        else:
            res = requests.get("http://" + parsedUrl.netloc + "/robots.txt", timeout=(5,7))
            if res.text is not None:
                uo = res.text
            else:
                uo = ""
    except RequestException as e:
        print("robots.txt inaccessible for site:",url)
        uo = ""

    return uo

# urllib implementation does only basic functionality
# It does not provide sitemap parsing
def robotsparse(url):
    rp = urllib.robotparser.RobotFileParser()

    status_code = 300
    max_red = 3
    rd = ""
    visited = set()
    while (status_code // 100)%10 == 3:
        if max_red <= 0:
            return '', ''
        rd = get_robots_data(url)
        if rd == "":
            sleep(5)
            max_red -= 1
            #Check redirect
            parsedUrl = urlparse(canonize_url(url))
            visited.add("http://"+parsedUrl.netloc)
            try:
                response = requests.head("http://"+parsedUrl.netloc, timeout=10)
                status_code = response.status_code
                if (status_code // 100)%10 == 3:
                    url = canonize_url(response.headers["Location"])
                    if "http://"+urlparse(url).netloc in visited:
                        break
            except:
                return '',''
            
        else:
            break

    # Parse according data
    rp.parse(rd.splitlines())

    # Find Sitemap.xml if exists
    sitemaps = re.findall("Sitemap:\s+([A-Za-z0-9\-\.\_\~\:\/\?\#\[\]\@\!\$\&\(\)\*\+\,\;\=\%]+)", rd)
    
    # For each sitemap if for some reason hosted on multiple urls
    # Get all location urls
    sitemap_contents = ""
    for sitemap in sitemaps:
        try:
            res = requests.get(sitemap, timeout=(5,7) )
            if res.text is not None:
                sitemap_contents += res.text
        except RequestException as e:
            print(e)
    
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