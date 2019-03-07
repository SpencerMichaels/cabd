from urllib.request import urlopen

from bs4 import BeautifulSoup

def get_soup(url):
  with urlopen(url) as response:
    return BeautifulSoup(response.read(), 'html5lib')
