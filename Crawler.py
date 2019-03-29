from database.models import *
from urllib.parse import urlparse
from processing import WrappedPool, create_pool_object
import re
from tools import *
from HTTPDownloaderWrapper import *
from tools import get_domain

# List of seed urls
seed_list = [
    # Compulsory
    "evem.gov.si",
    "e-uprava.gov.si",
    "podatki.gov.si",
    "e-prostor.gov.si",
    # Selected
    "www.arso.gov.si",
    "gu.gov.si",
    "mop.gov.si",
    "mju.gov.si",
    "www.ess.gov.si"
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
        pool = create_pool_object(processSiteUrlWrapper, session=self.session, max_workers=4, max_size=16)
        
        # Register callbacks
        # "website" expects a list with appropriate data
        pool.register_callback("website", self.process_website)
        # "add_to_frontier" contains same data as used by processing.py. 
        # It is a list of links
        pool.register_callback("add_to_frontier", self.process_links)
        # "documents" contains an array of documents
        pool.register_callback("documents", self.process_documents)

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

    def process_links(self, url, links):
        links = [canonize_url(link) for link in links]
        linkObjs = [Link(from_page=url, to_page=link) for link in links]
        self.session.add_all(linkObjs)
        self.session.commit()

    def process_website(self, url, website):
        domain = get_domain(url)
        site = self.session.query(Site).filter(Site.domain == domain).one()
        page = self.session.add(
            Page(
                site_id=site.id, 
                page_type_code=website["page_type"], 
                url=url, 
                html_content=website["content"], 
                http_status_code=website["status_code"],
                accessed_time=website["accessed_time"]
            )
        )
        self.session.commit()
        
        imageObjects = []
        #for image in website["images"]:
        #    imageObjects.append(Image(page_id=page.id, ))

        self.session.add_all(imageObjects)
        self.session.commit()
        page_data = self.session.add(PageData(page_id=page.id, data_type_code=website["data_type"])
        # self.session.query(Page).filter(Page.html_content == website).count() <= 0
        #print("website:", website)

    def process_documents(self, url, documents):
        pass

Crawler()