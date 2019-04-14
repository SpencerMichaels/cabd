import asyncio
import json
import re
from urllib.parse import urlparse

from book import Book, Chapter
import utils

NAME = 'TingChina'
DOMAINS = ['www.tingchina.com']

def can_handle(domain):
  return domain in DOMAINS

# Usually you'd have to log in to download from tingchina, but you can bounce
# off of lanren9's tc.php to get temporary download links with the right keys
async def get_chapter_url(session, book_id, chapter_id):
  raw_url = 'http://www.lanren9.com/xplayer/tc/tc.php?id=yousheng/%s/%s' % \
      (book_id, chapter_id)
  async with session.get(raw_url) as response:
    body = await response.content.read()
    return json.loads(body)['url']

async def get_chapter(session, book_id, chapter_id):
  raw_url = await get_chapter_url(session, book_id, str(chapter_id))

  url = urlparse(raw_url)
  title = url.path.split('/')[-1].split('.')[0]

  return Chapter(title, raw_url)

async def get_book(session, raw_url):
  # Get the main page for the book, which has links to all chapters
  soup = await utils.get_soup(session, raw_url)

  book01 = soup.find('div', {'class': 'book01'})
  title = book01.find('span').find('strong').text
  art_url = 'http://www.tingchina.com' + book01.find('img')['src']

  book_id = raw_url.split('_')[1].split('.')[0]
  last_chapter_href = soup.find('div', {'class': 'list'}).find_all('a')[-3]['href']
  last_chapter_id = last_chapter_href.split('_')[2].split('.')[0]
  chapter_ids = range(0, int(last_chapter_id)+1)

  tasks = map(lambda cid: get_chapter(session, book_id, cid), chapter_ids)
  chapters = await asyncio.gather(*tasks)

  print(title)

  return Book(title=title, art_url=art_url, chapters=chapters)

async def get_books_for_search(session, raw_url):
  soup = await utils.get_soup(session, raw_url)

  book_as = soup.find('dl', {'class': 'singerlist1'}).find_all('a')
  book_urls = [ 'http://www.tingchina.com/' + a['href'] for a in book_as ]

  return await asyncio.gather(
      *map(lambda book_url: get_book(session, book_url), book_urls))

# A link to an author page will be handled by batch-downloading all the books
# for that author. Otherwise, we treat the link as a single book.
async def get(session, url):
  if url.path.startswith('/yousheng'):
    return [ await get_book(session, url.geturl()) ]
  elif url.path.startswith('/search'):
    return await get_books_for_search(session, url.geturl())
  else:
    raise Exception('Not supported: ' + url.geturl())
