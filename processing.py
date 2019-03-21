# THREAD POOL
# Concurrent futures thread pool
import concurrent.futures
#from url_normalize import url_normalize
from multiprocessing import Queue
import sys, time, atexit, url


def canonize_url(url_string):
    url_parsed = url.URL.parse(url_string)
    url_cleaned = url_parsed.strip().defrag().deparam(['utm_source']).abspath().escape().canonical().utf8
    return url_cleaned

# Callbacks: ['site_processed', 'links_discovered']
# Pool wrapper
class WrappedPool:
    def __init__(self, func, max_workers, max_size, load_frontier):
        self.max_workers = max_workers
        self.func = func
        self.params_list=[]
        self.frontier = Queue()
        self.processed = set()
        
        #if load_frontier:
        #    self.load_frontier()
        

        # Callback dictionary
        self.callback = dict()

        atexit.register(self.exit_func)
    
    #def load_frontier(self):
    #    self.frontier.

    #def save_frontier(self):
    #    self.frontier.

    # Callback registration
    def register_callback(self, c_type, func):
        self.callback[c_type] = func

    def exit_func(self):
        # If queue, save to database
        ls = list()
        print(self.frontier.empty())
        while not self.frontier.empty():
            ls.append(self.frontier.get())
        print(ls)

    def execute_with_parameters(self, *params):
        self.params_list.append(params)
        self.exec()

    def execute_with_parameters_list(self, params):
        for param in params:
            self.params_list.append(param)
            print(param)
        self.exec()

    def exec(self):
        with concurrent.futures.ProcessPoolExecutor(max_workers=self.max_workers) as executor:            
            try:
                futures = {executor.submit(self.func, canonize_url(params) ): params for params in self.params_list}
                while futures:
                    fin,nfin = concurrent.futures.wait(futures, timeout=0.1, return_when=concurrent.futures.FIRST_COMPLETED)
                    if len(fin) > 0:
                        for f in list(fin):
                            futures.pop(f,None)
                            res = f.result()
                            if ("add_to_queue" in res):
                                for prm in res["add_to_queue"]:
                                    cprm = canonize_url(prm)
                                    if cprm not in self.processed:
                                        self.frontier.put(cprm)
                            for k in res:
                                if (k in self.callback):
                                    self.callback[k](res[k])
                            
                    
                    print("\033[K",end='\r')
                    print("Current frontier size:", str(self.frontier.qsize()), end='\r')
                    
                    while not self.frontier.empty() and len(futures) < self.max_size:
                        prms = self.frontier.get()
                        futures[executor.submit(self.func, canonize_url(prms))] = prms

                        
            except concurrent.futures.process.BrokenProcessPool as ex:
                print(ex)
                

# Pool creation function
def create_pool_object(func, max_workers=4, max_size=20, load_frontier=True):
    return WrappedPool(func, max_workers, max_size, load_frontier)




# EXAMPLE
# Out of file defined
#def fnc(url):
#    time.sleep(1)
#    return {"processed": [url, url, ...]}

#if len(sys.argv) > 0:
#    po = create_pool_object(fnc, max_size=8)
#    po.register_callback("processed", lambda x: print(x))
#    THEN
#    po.execute_with_parameters_list(["url1","url2","url3","url4","url5","url6","url7","url8"])
#    OR
#    po.execute_with_parameters(url1)