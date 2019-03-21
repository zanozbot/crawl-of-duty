from bs4 import BeautifulSoup
import aiohttp
import asyncio
from urllib.parse import urlparse
import urllib.robotparser

rp = urllib.robotparser.RobotFileParser()
URL = 'http://e-uprava.gov.si'
URL2 = 'http://e-uprava.gov.si/e-uprava/oglasnadeska.html'


def __init__(self, URL):
    self.URL = URL


async def getSiteContent(url):
    async with aiohttp.ClientSession() as session:
        parsedUrl = urlparse(url)
        rp.set_url(parsedUrl.scheme + "://" + parsedUrl.netloc + "/robots.txt")
        rp.read()
        if rp.can_fetch("*", url):
            async with session.get(url) as resp:
                text = await resp.read()
        else:
            return ""

    # print(BeautifulSoup(text.decode('utf-8'), 'html5lib'))
    return BeautifulSoup(text.decode('utf-8'), 'html5lib')


asyncio.run(getSiteContent(URL))
asyncio.run(getSiteContent(URL2))