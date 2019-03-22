from bs4 import BeautifulSoup
import aiohttp
import asyncio
from urllib.parse import urlparse
import urllib.robotparser
from enum import Enum

from selenium import webdriver
import pandas as pd

rp = urllib.robotparser.RobotFileParser()
URL = 'http://e-uprava.gov.si'
URL2 = 'http://e-uprava.gov.si/e-uprava/oglasnadeska.html'
URL3 = 'https://angular.io'
URL4 = 'https://reddit.com'

class ContentType(Enum):
    HTML = 0,
    HEAD = 1


async def getSiteContent(url, contentType = ContentType.HTML):
    async with aiohttp.ClientSession() as session:
        parsedUrl = urlparse(url)
        rp.set_url(parsedUrl.scheme + "://" + parsedUrl.netloc + "/robots.txt")
        rp.read()
        if rp.can_fetch("*", url):
            if contentType == ContentType.HTML:
                async with session.get(url) as resp:
                    text = await resp.read()
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


def seleniumGetContents(url):
    driver = webdriver.Chrome('C:/Users/Uporabnik/Documents/Git/crawl-of-duty/chromedriver.exe')
    driver.get(url)
    htmlContent = BeautifulSoup(driver.page_source, 'html5lib')
    # print(htmlContent)
    documents = []
    images = []
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


# asyncio.run(getSiteContent(URL, ContentType.HTML))
# asyncio.run(getSiteContent(URL, ContentType.HEAD))

# htmlContent, documents = asyncio.run(getSiteContent(URL3, ContentType.HTML))
# print(htmlContent)
# print(documents)

# html, doc, images = seleniumGetContents(URL4)

# print(html)
# print(doc)
# print (images)

# html, doc, images = seleniumGetContents(URL3)