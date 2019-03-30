# THREAD POOL
# Concurrent futures thread pool
import concurrent.futures
# Import synchronized Queue
from multiprocessing import Queue
# Import all ORM models
from database.models import *
import sys, time, atexit
from tools import *

# Pool wrapper
class WrappedPool:
    def __init__(self, func, max_workers, max_size, session):
        # Number of active workers
        self.max_workers = max_workers

        # Max number of urls in queue to be processed
        self.max_size = max_size

        # Session object
        self.session = session
        
        # Function to execute
        self.func = func

        # Parameter list
        self.params_list=[]

        # Frontier
        self.frontier = Queue()

        # Set of processed urls
        self.processed = set()

        # Callback dictionary
        self.callback = dict()

        # Register frontier save function at program exit
        atexit.register(self.save_frontier)

    # Bind a dictionary of robotparsers
    def bind_robotparsers(self, rp_dict):
        self.rp_dict = rp_dict

    # Bind a session
    def bind_session(self, sess):
        self.session = sess

    # Load frontier
    def load_frontier(self):
        rows = self.session.query(Frontier).all()
        self.params_list = [ (row.parent_url, row.url) for row in rows]
        self.session.query(Frontier).delete()
        self.session.commit()

    # Save frontier
    def save_frontier(self):
        ls = set()
        while not self.frontier.empty():
            urls = self.frontier.get()
            ls.add(Frontier(url=urls[1], parent_url=urls[0]))
        self.session.query(Frontier).delete()
        self.session.add_all(list(ls))
        self.session.commit()

    # Callback registration
    def register_callback(self, c_type, func):
        self.callback[c_type] = func

    # Start pool with parameters to pass to function
    def start_with_parameters(self, *params):
        self.params_list.append((None, params))
        self.exec()

    # Start pool with a list of parameters to pass to function
    def start_with_parameters_list(self, params):
        for param in params:
            self.params_list.append((None, param))
        self.exec()

    # Start pool with frontier
    def start_with_frontier(self):
        self.load_frontier()
        self.exec()

    # Get or make robotsparser
    def get_make_robotsparser(self, rp_url):
        if self.rp_dict is None:
            sites = self.session.query(Site).all()
            self.rp_dict = dict()
            for site in sites:
                rp = get_robotparser(site.robots_content)
                rp_dict[get_domain(site.domain)] = rp
        
        dmn = get_domain(rp_url)
        if dmn in self.rp_dict:
            return self.rp_dict[dmn]
        else:
            rp, sitemap = robotsparse(dmn)
            s = Site(domain=dmn, robots_content=rp, sitemap_content=sitemap)
            self.session.add(s)
            self.session.commit()
            rbp = get_robotparser(rp)
            self.rp_dict[dmn] = rbp
            return rbp

    # Execute pool process
    def exec(self):
        with concurrent.futures.ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            try:
                if len(self.params_list) > self.max_size:
                    for parm in self.params_list[self.max_size:]:
                        self.frontier.put(parm)
                    self.params_list = self.params_list[:self.max_size]
                futures = {executor.submit(self.func, canonize_url(params[1]), self.get_make_robotsparser(params[1]) ): params for params in self.params_list}
                while futures:
                    fin,nfin = concurrent.futures.wait(futures, timeout=0.1, return_when=concurrent.futures.FIRST_COMPLETED)
                    if len(fin) > 0:
                        for f in list(fin):
                            popped = futures.pop(f,None)
                            if popped is not None:
                                self.processed.add(popped[1])
                            res = f.result()
                            if ("add_to_frontier" in res):
                                res["add_to_frontier"] = [canonize_url(pr, popped[1]) for pr in res["add_to_frontier"]]
                                for prm in res["add_to_frontier"]:
                                    prm_not_in_db = self.session.query(Page).filter(Page.url == prm).first() is None
                                    if prm_not_in_db and prm not in self.processed:
                                        self.frontier.put((popped[1], prm))
                                        self.processed.add(prm)
                                
                            for k in res:
                                if (k in self.callback):
                                    self.callback[k](popped[1], popped[0], res[k])
                            
                    
                    print("\033[K",end='\r')
                    print("# in frontier:", str(self.frontier.qsize()), end='\r')
                    
                    while not self.frontier.empty() and len(futures) < self.max_size:
                        prms = self.frontier.get()
                        prm_not_in_db = self.session.query(Page).filter(Page.url == prms[1]).first() is None
                        if prm_not_in_db:
                            futures[executor.submit(self.func, canonize_url(prms[1]),  self.get_make_robotsparser(prms[1]))] = prms

                for l in range(self.max_size):
                    executor.submit(self.func, None, None)

            except concurrent.futures.process.BrokenProcessPool as ex:
                print(ex)
                

# Pool creation function
def create_pool_object(func, max_workers=4, max_size=16, session=None):
    return WrappedPool(func, max_workers, max(max_size, max_workers), session)