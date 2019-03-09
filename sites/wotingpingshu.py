import asyncio
import re

from book import Book, Chapter

import utils

NAME = '我听评书网'
DOMAINS = ['www.wotingpingshu.com']

def can_handle(domain):
  return domain in DOMAINS

# Get chapter metadata and the audio link from a chapter 'li' element.
# The chapter title does not appear on its own in any element of the 'play
# audio' page, so we take the original 'li' here and extract the title from it.
async def get_chapter(session, li):
  title = li.find('div', {'class': 'psList'}).text

  dl_page_url = li.find_all('a', {'class': 'button'})[1]['href']
  soup = await utils.get_soup(session, 'http:' + dl_page_url)
  url = soup.find('div', {'class': 'downsubmit'}).a['href']

  return Chapter(title=title, url=url)

async def get_book(session, url):
  soup = await utils.get_soup(session, url.geturl())

  # Basic book metadata
  title = soup.find('span', {'class': 'a-btn-text'}).text
  art_url = soup.find('div', {'class': 'contDetail'}) \
                .find('img', {'class': 'img'})['src']

  # Get the full list of 'li' (HTML list) elements containing the chapter links
  songlist = soup.find('div', {'class': 'songlist'})
  lis = songlist.ul.find_all(recursive=False)

  # Extract audio links from the chapter pages
  tasks = map(lambda li: get_chapter(session, li), lis)
  chapters = await asyncio.gather(*tasks)

  return Book(title=title, art_url=art_url, chapters=chapters)

# This site doesn't have an "author" page; only handle single books.
async def get(session, url):
  return [ await get_book(session, url) ]
