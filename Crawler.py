from database.models import *
from urllib.parse import urlparse
from processing import WrappedPool, create_pool_object
import re
from tools import *
from HTTPDownloaderWrapper import *
from tools import get_domain
import hashlib
from multiprocessing import freeze_support

# List of seed urls
seed_list = [
    # Compulsory
    "evem.gov.si",
    "e-uprava.gov.si",
    "podatki.gov.si",
    "e-prostor.gov.si",
    # Selected
    # "www.arso.gov.si",
    # "www.gu.gov.si",
    # "mop.gov.si",
    # "mju.gov.si",
    # "www.ess.gov.si"
]

class Crawler:
    def __init__(self):
        # Create session from Session object
        print("- INITIALIZING DATABASE CONNECTION -")
        self.session = Session()

        # Get robots.txt and sitemap.xml data if available and not in db
        seedObjs = []
        sites = []
        for seed in seed_list:
            seed = canonize_url(seed)
            if self.session.query(Site).filter(Site.domain == seed).count() <= 0:
                rp, sitemap = robotsparse(seed)
                s = Site(domain=seed, robots_content=rp, sitemap_content=sitemap)
                sites.append(s)

        if len(sites) > 0:
            self.session.add_all(sites)
            self.session.commit()

        # Create process pool
        pool = create_pool_object(processSiteUrlWrapper, session=self.session, max_workers=8, max_size=16)
        
        # Register callbacks
        # "website" expects a list with appropriate data
        pool.register_callback("website", self.process_website)
        # "documents" contains an array of documents
        pool.register_callback("document", self.process_documents)

        # Get the number of urls in frontier
        rows = self.session.query(Frontier).count()

        # Get all sites and create robotparser dictionary
        sites = self.session.query(Site).all()
        rp_dict = dict()
        for site in sites:
            rp = get_robotparser(site.robots_content)
            rp_dict[get_domain(site.domain)] = rp
        
        # Bind a dictionary of robotparsers
        pool.bind_robotparsers(rp_dict)

        # Load from database or start with seed lsit
        if rows > 0:
            pool.start_with_frontier()
        else:
            # Get all site data
            seeds = []
            for site in sites:
                seeds.append(site.domain)
                if site.sitemap_content is not None and site.sitemap_content != '':
                    nrmlzd = get_sitemap_locations(site.sitemap_content)
                    for nrm in nrmlzd:
                        seeds.append(nrm)
            pool.start_with_parameters_list(seeds)

    def process_links(self, url, parentUrl, links):
        links = [canonize_url(link) for link in links]
        

    def process_website(self, url, parentUrl, website):
        page = self.session.query(Page).filter(Page.url == url).first()
        parentPage = self.session.query(Page).filter(Page.url == parentUrl).first()
        if (page is not None and 
            parentPage is not None and 
            self.session.query(Link).filter(Link.from_page == parentPage.id).filter(Link.to_page == page.id).first() is not None):
            return
        print(url)
        domain = get_domain(url)
        site = self.session.query(Site).filter(Site.domain == domain).first()
        if site is None:
            rp, sitemap = robotsparse(domain)
            site = Site(domain=domain, robots_content=rp, sitemap_content=sitemap)
            self.session.add(site)
            self.session.flush()

        html_hash = hashlib.sha512(website["content"].encode('utf-8')).hexdigest()
        page = self.session.query(Page).filter(Page.url == url).first()
        if page is None:
            page = self.session.query(Page).filter(Page.html_hash == html_hash).first()
            if page is None:
                page = Page(
                    site_id=site.id, 
                    page_type_code=website["page_type"], 
                    url=url, 
                    html_content=website["content"],
                    html_hash=html_hash,
                    http_status_code=website["status_code"],
                    accessed_time=website["time_accessed"]
                )
                self.session.add(page)
                self.session.flush()
            else:
                page = Page(
                    site_id=site.id, 
                    page_type_code=website["page_type"], 
                    url=url, 
                    html_content=None,
                    html_hash=None,
                    http_status_code=website["status_code"],
                    accessed_time=website["time_accessed"]
                )
                self.session.add(page)
                self.session.flush()
        else:
            return
    
        if parentPage is not None and self.session.query(Link).filter(Link.from_page == parentPage.id).filter(Link.to_page == page.id).first() is None:
            linkObj = Link(from_page=parentPage.id, to_page=page.id)
            self.session.add(linkObj)
            self.session.commit()

        if "images" in website:
            image_mimes = {".png", ".pgm", ".jpeg", ".gif", ".bmp", ".tiff", ".svg", ".webp"}
            imageObjects = []
            for image in website["images"]:
                encoded_content = b''
                try:
                    encoded_content = bytearray(image[0].encode('ascii'))
                except:
                    try:
                        encoded_content = bytearray(image[0].encode('utf-8'))
                    except:
                        print("CANNOT ENCODE IMAGE INTO BYTE ARRAY")
                        return
                mime_type = get_mime_type_from_header(image[1])
                if mime_type in image_mimes:
                    imageObjects.append(Image(page_id=page.id, filename='', content_type=mime_type, data=encoded_content, accessed_time=image[3]))

            self.session.add_all(imageObjects)
            self.session.commit()

        self.session.flush()

    def process_documents(self, url, parentUrl, document):
        domain = get_domain(url)
        site = self.session.query(Site).filter(Site.domain == domain).first()
        if site is None:
            rp, sitemap = robotsparse(domain)
            site = Site(domain=domain, robots_content=rp, sitemap_content=sitemap)
            self.session.add(site)
            self.session.flush()
        
        page = self.session.query(Page).filter(Page.url == url).first()
        if page is None:
            page = Page(
                site_id=site.id, 
                page_type_code=document["page_type"], 
                url=url, 
                html_content=None,
                html_hash=None,
                http_status_code=document["status_code"],
                accessed_time=document["time_accessed"]
            )
            self.session.add(page)
            self.session.flush()
        
        encoded_content = b''
        try:
            encoded_content = bytearray(document["content"].encode('ascii'))
        except:
            try:
                encoded_content = bytearray(document["content"].encode('utf-8'))
            except:
                print("CANNOT ENCODE DOCUMENT INTO BYTE ARRAY")
                return
        page_data = self.session.add(
            PageData(
                page_id=page.id,
                data_type_code=document["data_type"],
                data=encoded_content
            )
        )
        self.session.commit()

        parentPage = self.session.query(Page).filter(Page.url == url).first()
        if parentPage is not None and self.session.query(Link).filter(Link.from_page == parentPage.id).filter(Link.to_page == page.id).first() is None:
            linkObj = Link(from_page=parentPage.id, to_page=page.id)
            self.session.add(linkObj)
            self.session.commit()
            self.session.flush()

if __name__ == '__main__':
    freeze_support()
    Crawler()

