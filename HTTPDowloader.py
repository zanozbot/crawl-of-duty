from bs4 import BeautifulSoup
import aiohttp
from urllib.parse import urlparse
from urllib.request import urlopen
import urllib.robotparser
from enum import Enum
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
import sys, re
import xml.etree.ElementTree as ET

rp = urllib.robotparser.RobotFileParser()
URL = 'http://e-uprava.gov.si'
URL2 = 'http://e-uprava.gov.si/e-uprava/oglasnadeska.html'
URL3 = 'https://angular.io'
URL4 = 'https://reddit.com'
URL5 = 'http://www.e-prostor.gov.si'
pdfURL = 'https://arxiv.org/pdf/1808.07042.pdf'


# Drivers linux/windows/osx
platform_driver = ''
if sys.platform.startswith('linux'):
    platform_driver = './platform_dependent/linux_chromedriver'
elif sys.platform.startswith('win') or sys.platform.startswith('cygwin'):
    platform_driver = './platform_dependent/win_chromedriver.exe'
elif sys.platform.startswith('darwin'):
    platform_driver = './platform_dependent/osx_chromedriver'

# Instantiate headless chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome(executable_path=platform_driver, options=chrome_options)


class ContentType(Enum):
    HTML = 0,
    HEAD = 1


async def getSiteContent(url, contentType = ContentType.HTML):
    async with aiohttp.ClientSession() as session:
        parsedUrl = urlparse(url)
        print(parsedUrl)
        rp.set_url(parsedUrl.scheme + "://" + parsedUrl.netloc + "/robots.txt")
        rp.read()
        if rp.can_fetch("*", url):
            if contentType == ContentType.HTML:
                async with session.get(url) as resp:
                    text = await resp.read()
                    print(text)
            elif contentType == ContentType.HEAD:
                async with session.get(url) as resp:
                    text = resp.headers
        else:
            return ""

    if contentType == ContentType.HTML:
        # print(BeautifulSoup(text.decode('utf-8'), 'html5lib'))
        htmlContent = BeautifulSoup(text.decode('utf-8'), 'html5lib')
        documents = []
        images = []
        for link in htmlContent.find_all('img'):
            current_link = link.get('src')
            if current_link:
                images.append(current_link)
        for link in htmlContent.find_all('a'):
            current_link = link.get('href')
            if current_link :
                if current_link.endswith('pdf') \
                            or current_link.endswith('doc') \
                            or current_link.endswith('docx') \
                            or current_link.endswith('doc') \
                            or current_link.endswith('ppt') \
                            or current_link.endswith('pptx'):
                    documents.append(current_link)
        return htmlContent, documents, images
    elif contentType == ContentType.HEAD:
        # print(text.decode('utf-8'))
        return text, [], []


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

def seleniumGetContents(url):
    driver.get(url)
    robotsparse(url)
    htmlContent = BeautifulSoup(driver.page_source, 'html5lib')
    # print(htmlContent)
    documents = []
    images = []
    parsedUrl = urlparse(url)
    rp.set_url(parsedUrl.scheme + "://" + parsedUrl.netloc + "/robots.txt")
    rp.read()
    print(rp)
    return
    if rp.can_fetch("*", url):
        for link in htmlContent.find_all('img'):
            current_link = link.get('src')
            if current_link:
                images.append(current_link)
        for link in htmlContent.find_all('a'):
            current_link = link.get('href')
            if current_link:
                if current_link.endswith('pdf') \
                        or current_link.endswith('doc') \
                        or current_link.endswith('docx') \
                        or current_link.endswith('doc') \
                        or current_link.endswith('ppt') \
                        or current_link.endswith('pptx'):
                    documents.append(current_link)
        driver.close()
    return htmlContent, documents, images

async def getBinaryFile(url):
    async with aiohttp.ClientSession() as session:
        parsedUrl = urlparse(url)
        print(parsedUrl)
        rp.set_url(parsedUrl.scheme + "://" + parsedUrl.netloc + "/robots.txt")
        rp.read()
        if rp.can_fetch("*", url):
            async with session.get(url) as resp:
                text = await resp.read()
                return text

# asyncio.run(getSiteContent(URL, ContentType.HTML))
# asyncio.run(getSiteContent(URL, ContentType.HEAD))

# htmlContent, documents = asyncio.run(getSiteContent(URL3, ContentType.HTML))
# print(htmlContent)
# print(documents)

# html, doc, images = seleniumGetContents(URL4)

# print(html)
# print(doc)
# print (images)

html, doc, images = seleniumGetContents(URL5)
print(html)
print(doc)
print(images)

# html, doc, images = asyncio.run(getSiteContent(pdfURL, ContentType.HTML))

# binary = asyncio.run(getBinaryFile(pdfURL))
# print(binary)