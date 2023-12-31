from urllib.request import urlopen
from urllib.error import HTTPError
from urllib.error import URLError
from bs4 import BeautifulSoup
from pymongo import MongoClient
import re

# MongoDB client setup
def connectDataBase():
    client = MongoClient(host="localhost", port=27017)
    db = client.searchengine
    return db, client

"""
Determines if target page is found based off faculty page pattern "College of Business Administration"
params: html (string)
returns: Found(boolean)
"""
def is_target_page(html):
    if html == None:
        return False
    bs = BeautifulSoup(html, 'html.parser')
    
    if bs.find('div', class_='fac-info') == None:
        return False
    title_comparison = bool(bs.find('div', class_='fac-info').find('span', class_='title-dept').find(string=re.compile('.*College of Business Administration.*')))
    return title_comparison
    
    
# Function to retrieve and store page in MongoDB
def store_page(url, html):
    # Store page in MongoDB: url, html
    pages_collection.insert_one({'url': url, 'html': html})
                       
# Function to grab URLs, Arg HTML, returns List of Urls(string list)
def parse(html):
    bs = BeautifulSoup(html, 'html.parser')
    links = bs.find_all('a', href = True)
    return links

# Frontier class for crawling based off Queue 
class Frontier:
    def __init__(self, seed_urls):
        self.visited = set()            #keep track of visited pages
        self.queue = list(seed_urls)    #implement queue

    # add url to queue
    def add_url(self, url):
        if url not in self.visited:
            self.queue.append(url)
            self.visited.add(url)

    # return next url in queue
    def next_url(self):
        return self.queue.pop(0) if self.queue else None

    # No more links to visit
    def done(self):
        return len(self.queue) == 0
        
    #clear list once all targets found
    def clear(self):
        self.queue.clear()
        
def crawlerThread(frontier, num_targets):
    targets_found = 0    

    while not frontier.done():
        url = frontier.next_url()
        
        # Add URLS to visted set if not added (initial seed)
        if url not in frontier.visited:
            frontier.visited.add(url)
            
        # OPEN URLS AND RAISE EXCEPTIONS
        try:
            html = urlopen(url)
            html = html.read()
            html = html.decode(encoding="iso-8859-1")

        except HTTPError as e:
            print("HTTP error")
            continue
        except URLError as e:
            print("Error server not found: ")
            continue
        except Exception as e:
            print("Unknown Error")
            continue
        else:
            store_page(url, html)

            

        # Stop Crawl if minimimum of num_targets(10-22) is met
        if is_target_page(html):
            targets_found += 1
            if targets_found == num_targets:
                frontier.clear()
                break

        # Add links to queue from current page
        for link in parse(html):
            templink = link['href']

            if (re.match("^https://www.cpp.edu", templink) == None):
                templink = "https://www.cpp.edu" + templink
            frontier.add_url(templink)

# Initialize Database
db, client = connectDataBase()
pages_collection = db.pages

# Seed URLs for each department
seed_urls = ['https://www.cpp.edu/cba/international-business-marketing/index.shtml']
    
# Number of target faculty pages to find (this will be department-specific)
num_targets = 22

# Initialize frontier with seed URLs
frontier = Frontier(seed_urls)

# Start crawling
crawlerThread(frontier, num_targets)

# Close the MongoDB client when done
client.close()

