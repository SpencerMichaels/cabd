import asyncio
import json
import re
from urllib.parse import urlparse

from book import Book, Chapter
import utils

NAME = '喜马拉雅'
DOMAINS = ['www.ximalaya.com']

def can_handle(domain):
  return domain in DOMAINS

async def get_chapter(session, track_id):
  obj = await utils.get_json(
      session, 'http://mobile.ximalaya.com/v1/track/baseInfo?trackId=' + track_id)

  return Chapter(obj['title'], obj['playPathAacv224'])

async def accum_for_each_page(session, base_url, p1_soup, func):
  pagination = p1_soup.find('ul', {'class': 'pagination-page'})

  # Call func on first page
  accum = func(p1_soup)

  if pagination:
    num_pages = len(pagination.find_all('li'))
    for i in range(2, num_pages+1):
      page_id = ('p%d/' % (i))
      if not base_url.endswith('/'):
        base_url += '/'
      soup = await utils.get_soup(session, base_url + page_id)
      accum += func(soup) # Call func on page 2+

  return accum

async def get_book(session, raw_url):
  # TODO: do this for each page
  soup = await utils.get_soup(session, raw_url)

  cover_img = soup.find('div', {'class': 'album-info'}).find('img')
  title = cover_img['alt']
  art_url = cover_img['src'][2:]

  def get_track_ids(soup):
    sound_list = soup.find('div', {'class': 'sound-list'})
    sounds = sound_list.find_all('li', {'class': '_OO'})
    track_ids = [ item.find('a')['href'].split('/')[-1] for item in sounds ]
    return track_ids

  track_ids = await accum_for_each_page(session, raw_url, soup, get_track_ids)

  tasks = map(lambda tid: get_chapter(session, tid), track_ids)
  chapters = await asyncio.gather(*tasks)

  return Book(title=title, art_url=art_url, chapters=chapters)

PAGE_RE = re.compile('p[0-9]')

async def get_books_from_search(session, url):
  soup = await utils.get_soup(session, url.geturl())
  base_url = '%s://%s' % (url.scheme, url.netloc)

  search_base_url = url.geturl().split('/')[:-1] \
    if PAGE_RE.match(url.path.split('/')[-1]) \
    else url.geturl()

  def get_book_ids(soup):
    ssp = soup.find('div', {'class': 'search-sub-page'})
    titles = ssp.find_all('a', {'class': 'xm-album-title'})
    return [ base_url + title['href'] for title in titles ]

  book_urls = await accum_for_each_page(session, search_base_url, soup, get_book_ids)

  tasks = map(lambda book_url: get_book(session, book_url), book_urls)
  chapters = await asyncio.gather(*tasks)

async def get(session, url):
  if url.path.startswith('/youshengshu'):
    return [ await get_book(session, url.geturl()) ]
  elif url.path.startswith('/search'):
    return [ await get_books_from_search(session, url) ]
  else:
    raise Exception('Not supported: ' + url.geturl())
