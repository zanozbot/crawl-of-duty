from tools import platform_driver, chrome_options
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from HTTPDownloader import *
from multiprocessing import Process, Queue, Manager
import multiprocessing as mp
from database.models import *
import sys, time, atexit
from tools import *
from datetime import datetime
import hashlib
from time import sleep


LOCK = mp.Lock()
manager = Manager()

class P(Process):
    def __init__(self, rp_dict, frontiers, frontier_timers, frontier_time_limits, processed):
        self.frontiers = frontiers
        self.frontier_timers = frontier_timers
        self.frontier_time_limits = frontier_time_limits
        self.rp_dict = rp_dict
        self.processed = processed
        super(P, self).__init__()

    def frontiers_empty(self):
        keys = list(self.frontiers.keys())
        for k in keys:
            if self.frontiers[k]:
                return False
        return True

    def run(self):
        self.driver = webdriver.Chrome(executable_path=platform_driver, options=chrome_options)
        self.driver.set_page_load_timeout(5)
        self.driver.set_script_timeout(7)
        self.session = Session()

        while not self.frontiers_empty():
            # Sleep while waiting
            sleep(0.1)

            # Get all keys from dictionary
            # This is to avoid error if dict size
            # changes while iterating
            keys = list(self.frontiers.keys())

            # Acquire exclusive lock while editing queues
            LOCK.acquire()
            prms = None
            rp = None
            for k in keys:
                if self.frontiers[k]:
                    if k not in self.frontier_time_limits:
                        self.get_make_robotsparser(k)

                    if (datetime.now() - self.frontier_timers[k]).total_seconds() < self.frontier_time_limits[k]:
                        continue
                    
                    prms = self.frontiers[k][0]
                    rp = self.get_make_robotsparser(prms[1])
                    del self.frontiers[k][0]

                    prm_not_in_db = self.session.query(Page).filter(Page.url == prms[1]).first() is None
                    if prm_not_in_db and prms not in self.processed:
                        # take url, set time
                        self.processed[prms] = True
                        self.frontier_timers[k] = datetime.now()
                    else:
                        # url was already processed
                        prms = None
                    break
            LOCK.release()

            if rp is not None and prms is not None:
                res = processSiteUrl(prms[1], rp, self.driver)
                print(prms[1])
                if "add_to_frontier" in res:
                    res["add_to_frontier"] = [canonize_url(pr, prms[1]) for pr in res["add_to_frontier"]]
                    LOCK.acquire()
                    for prm in res["add_to_frontier"]:
                        prm_not_in_db = self.session.query(Page).filter(Page.url == prm).first() is None
                        if prm not in self.processed and prm_not_in_db:
                            dmn = get_domain(prm)
                            if dmn not in self.frontiers:
                                self.frontiers[dmn] = manager.list()
                                self.frontier_timers[dmn] = datetime.now()
                                self.get_make_robotsparser(dmn)
                            self.frontiers[dmn].append((prms[1], prm))
                            self.processed[prm] = True
                    LOCK.release()

                if "website" in res:
                    self.process_website(prms[1], prms[0], res["website"])
                if "document" in res:
                    self.process_documents(prms[1], prms[0], res["document"])

        self.driver.close()
        self.session.close()

    # Sets time limit for domains
    def set_time_limit(self, domain, rbp):
        cd = rr = None
        try:
            rr = rbp.request_rate("*")
        except:
            pass
        try:
            cd = rbp.crawl_delay("*")
        except:
            pass
        if rr is not None:
            self.frontier_time_limits[domain] = rr.seconds/rr.requests
        elif cd is not None:
            self.frontier_time_limits[domain] = cd
        else:
            self.frontier_time_limits[domain] = 5

    # Get or make robotsparser
    def get_make_robotsparser(self, rp_url):
        dmn = ""
        if self.rp_dict is None:
            sites = self.session.query(Site).all()
            self.rp_dict = self.manager.dict()
            for site in sites:
                rp = get_robotparser(site.robots_content)
                dmn = get_domain(site.domain)
                self.rp_dict[dmn] = rp
                self.set_time_limit(dmn, self.rp_dict[dmn])

        dmn = get_domain(rp_url)
        
        if dmn in self.rp_dict:
            if dmn not in self.frontier_time_limits:
                self.set_time_limit(dmn, self.rp_dict[dmn])
        else:
            dmsite = self.session.query(Site).filter(Site.domain == dmn).first()
            if dmsite is not None:
                self.rp_dict[dmsite.domain] = get_robotparser(dmsite.robots_content)
                self.set_time_limit(dmsite.domain, self.rp_dict[dmsite.domain])
            else:
                rp, sitemap = robotsparse(dmn)
                s = Site(domain=dmn, robots_content=rp, sitemap_content=sitemap)
                self.session.add(s)
                self.session.commit()
                self.session.flush()
                rbp = get_robotparser(rp)
                self.rp_dict[dmn] = rbp
                self.set_time_limit(dmn, self.rp_dict[dmn])
        return self.rp_dict[dmn]

    def process_website(self, url, parentUrl, website):
        page = self.session.query(Page).filter(Page.url == url).first()
        parentPage = self.session.query(Page).filter(Page.url == parentUrl).first()
        if (page is not None and 
            parentPage is not None and 
            self.session.query(Link).filter(Link.from_page == parentPage.id).filter(Link.to_page == page.id).first() is not None):
            return
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
                    imageObjects.append(Image(page_id=page.id, filename=image[4], content_type=mime_type, data=encoded_content, accessed_time=image[3]))
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

# Pool wrapper
class WrappedPool:
    def __init__(self, max_workers, max_size, session):
        self.manager = Manager()

        # Number of active workers
        self.max_workers = max_workers

        # Max number of urls in queue to be processed
        self.max_size = max_size

        # Session object
        self.session = session

        # Parameter list
        self.params_list=[]

        # Frontier
        self.frontiers = self.manager.dict()
        self.frontier_timers = self.manager.dict()
        self.frontier_time_limits = self.manager.dict()

        self.rp_dict = self.manager.dict()

        # Set of processed urls
        self.processed = self.manager.dict()

        # Callback dictionary
        self.callback = self.manager.dict()

    # Bind a dictionary of robotparsers
    def bind_robotparsers(self, rp_dict):
        for (key,value) in rp_dict.items():
            self.rp_dict[key] = value

    # Bind a session
    def bind_session(self, sess):
        self.session = sess

    # Sets time limit for domains
    def set_time_limit(self, domain, rbp):
        cd = rr = None
        try:
            rr = rbp.request_rate("*")
        except:
            pass
        try:
            cd = rbp.crawl_delay("*")
        except:
            pass
        if rr is not None:
            self.frontier_time_limits[domain] = rr.seconds/rr.requests
        elif cd is not None:
            self.frontier_time_limits[domain] = cd
        else:
            self.frontier_time_limits[domain] = 5

    # Load frontier
    def load_frontier(self):
        rows = self.session.query(Frontier).all()
        self.params_list = []
        for row in rows:
            dmn = get_domain(row.url)
            if dmn not in self.frontiers:
                self.frontiers[dmn] = self.manager.list()
                self.frontier_timers[dmn] = datetime.now()
                self.get_make_robotsparser(dmn)
                
            self.frontiers[dmn].put((row.parent_url, row.url))

        if len(rows) > 0:
            self.params_list = [ (rows[0].parent_url, rows[0].url)]
        self.session.query(Frontier).delete()
        self.session.flush()

    # Save frontier
    def save_frontier(self):
        ls = list()
        for (key,front) in self.frontiers.items():
            if front:
                urls = set(front)
                ls.append(Frontier(url=urls[1], parent_url=urls[0]))
        self.session.query(Frontier).delete()
        self.session.add_all(ls)
        self.session.flush()

    # Callback registration
    def register_callback(self, c_type, func):
        self.callback[c_type] = func

    # Start pool with parameters to pass to function
    def start_with_parameters(self, *params):
        self.params_list.append((None, params))
        self.run()

    # Start pool with a list of parameters to pass to function
    def start_with_parameters_list(self, params):
        for param in params:
            self.params_list.append((None, param))
        self.run()

    # Start pool with frontier
    def start_with_frontier(self):
        self.load_frontier()
        self.run()

    # Get or make robotsparser
    def get_make_robotsparser(self, rp_url):
        LOCK.acquire()
        dmn = ""
        if self.rp_dict is None:
            sites = self.session.query(Site).all()
            self.rp_dict = self.manager.dict()
            for site in sites:
                rp = get_robotparser(site.robots_content)
                dmn = get_domain(site.domain)
                self.rp_dict[dmn] = rp
                self.set_time_limit(dmn, self.rp_dict[dmn])
        else:
            dmn = get_domain(rp_url)
        
        if dmn in self.rp_dict:
            if dmn not in self.frontier_time_limits:
                self.set_time_limit(dmn, self.rp_dict[dmn])
        else:
            dmsite = self.session.query(Site).filter(Site.domain == dmn).first()
            if dmsite is not None:
                self.rp_dict[dmsite.domain] = get_robotparser(dmsite.robots_content)
                self.set_time_limit(dmsite.domain, self.rp_dict[dmsite.domain])
            else:    
                rp, sitemap = robotsparse(dmn)
                s = Site(domain=dmn, robots_content=rp, sitemap_content=sitemap)
                self.session.add(s)
                self.session.commit()
                self.session.flush()
                rbp = get_robotparser(rp)
                self.rp_dict[dmn] = rbp
                self.set_time_limit(dmn, self.rp_dict[dmn])
        LOCK.release()
        return self.rp_dict[dmn]

    def run(self):
        for parm in self.params_list:
            dmn = get_domain(parm[1])
            if dmn not in self.frontiers:
                self.frontiers[dmn] = self.manager.list()
                self.frontier_timers[dmn] = datetime.now()
                self.get_make_robotsparser(dmn)
            self.frontiers[dmn].append(parm)

        workers = []
        for r in range(self.max_workers):
            worker = P(self.rp_dict, self.frontiers, self.frontier_timers, self.frontier_time_limits, self.processed)
            workers.append(worker)
            worker.start()
        
        print(len(workers))
        for worker in workers:
            worker.join()



def create_pool(max_workers=4, max_size=16, session=None):
    return WrappedPool(max_workers, max(max_size, max_workers), Session() if session is None else session)