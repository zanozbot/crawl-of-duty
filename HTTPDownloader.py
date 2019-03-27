from bs4 import BeautifulSoup
import aiohttp
import sys, re, atexit
import xml.etree.ElementTree as ET
from tools import *
import multiprocessing
from multiprocessing import Manager
import sys
from signal import signal, SIGTERM, SIGQUIT, SIGKILL, SIGINT
# Selenium
from selenium.webdriver.chrome.options import Options
from selenium import webdriver

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

driver_list = dict()

def processSiteUrl(url, robotsparser):
    # Access chrome instance coupled with this worker
    # or create if not running
    pid = multiprocessing.current_process().pid
    driver = None
    if pid not in driver_list:
        driver = driver_list[pid] = webdriver.Chrome(executable_path=platform_driver, options=chrome_options)
    else:
        driver = driver_list[pid]

    # Last time it is called
    # kill driver
    if url is None:
        driver = driver_list.pop(pid)
        driver.quit()
        return {}

    # Call appropriate code


    # return a dictionary with appropriate values
    # "add_to_frontier" should be an array of urls found on the website.
    # They do not need to be canonized, that is taken care of in processing.py
    # other keys are optional. For each key a callback can be specified that
    # gets called when returned. An example of that is in Crawler.py
    return {"add_to_frontier" : [], "website" : dict(), "documents" : [], "images" : []}


async def getSiteContent(url, robotsparser, contentType = ContentType.HTML):
    async with aiohttp.ClientSession() as session:
        rp, locations, sitemap = robotsparse(url)
        if robotsparser.can_fetch("*", url):
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

def seleniumGetContents(url, robotsparser, driver):
    driver.get(url)
    htmlContent = BeautifulSoup(driver.page_source, 'html5lib')
    # print(htmlContent)
    documents = []
    images = []
    rp, locations, sitemap = robotsparse(url)
    if robotsparser.can_fetch("*", url):
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

async def getBinaryFile(url, robotsparser):
    async with aiohttp.ClientSession() as session:
        rp, locations, sitemap = robotsparse(url)
        if robotsparser.can_fetch("*", url):
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

#html, doc, images = seleniumGetContents(URL5)
#print(html)
#print(doc)
#print(images)

# html, doc, images = asyncio.run(getSiteContent(pdfURL, ContentType.HTML))

# binary = asyncio.run(getBinaryFile(pdfURL))
# print(binary)