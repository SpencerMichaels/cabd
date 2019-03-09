import asyncio
from dataclasses import dataclass, field
import json
import re

from book import Book, Chapter
import utils

NAME = '懒人听书'
DOMAINS = ['www.lanren9.com']

PAGENUM_REGEX = re.compile('^.*-([0-9]+).html$')

@dataclass
class PlayData:
  title: str
  ref: str
  fmt: str

def can_handle(domain):
  return domain in DOMAINS

# Given a playdata ID, get a link to the actual audio file via tc.php, which
# responds with a JSON object whose only element is 'url'.
async def get_chapter_url(session, playdata_id):
  raw_url = 'http://www.lanren9.com/xplayer/tc/tc.php?id=' + playdata_id
  async with session.get(raw_url) as response:
    body = await response.content.read()
    return json.loads(body)['url']

async def get_chapters_playdata(session, raw_url):
  # The URL points to a small JS snippet that contains a single variable
  # declaration: the list of playdata items
  async with session.get(raw_url) as response:
    body = await response.content.read()
    entries = body[body.find(b'\'tudou\',[')+9:body.find(b']')].split(b',')

    # Each item is formatted like 'title$ref$format'. Sometimes the title is
    # unicode-escaped, and sometimes it's utf8; need to detect and decode
    # appropriately.
    def extract_playdata(entry):
      sections = entry[1:-1].split(b'$', 3)
      utf8_decode = lambda s: s.decode('utf-8')
      ref_decoder = 'unicode_escape' \
          if sections[0].startswith(b'\\') \
          else 'utf-8'
      return PlayData(sections[0].decode(ref_decoder),
                      *map(utf8_decode, sections[1:]))

    return map(extract_playdata, entries)

async def get_book(session, raw_url):
  # Get the main page for the book, which has links to all chapters
  soup = await utils.get_soup(session, raw_url)

  # Get basic book metadata
  art = soup.find('div', {'class': 'detail-pic'}).img
  title = art['alt']
  art_url = art['src']

  # Get the href to the 'play' page for the first chapter. The name 'player_1'
  # is disingenuous; it's actually the div holding the list of chapter links.
  base = '/'.join(raw_url.split('/', 3)[:3])
  first_chapter_href = soup.find(id='player_1').find('a')['href']
  first_chapter_soup = await utils.get_soup(session, base + first_chapter_href)

  # All the track data is present on every page in this JS snippet
  playdata_path = first_chapter_soup.find(id='bo') \
                               .find('script', {'type': 'text/javascript'})['src']

  # Extract chapter playdata from track data: title, link, and format
  chapters_playdata = await get_chapters_playdata(session, base + playdata_path)

  # Most playdata gives the audio URL directly, but a few give a 'tc' ID that
  # must be submitted to tc.php to look up the audio URL.
  async def playdata_to_chapter(playdata):
    url = await get_chapter_url(session, playdata.ref) \
            if playdata.fmt == 'tc' \
            else playdata.ref
    return Chapter(title=playdata.title, url=url)

  return Book(title=title, art_url=art_url,
              chapters=await asyncio.gather(*map(playdata_to_chapter, chapters_playdata)))

async def get_books_for_author(session, url):
  # Get the author's first page. There may be more pages listing more books.
  raw_url = url.geturl()
  first_page_soup = await utils.get_soup(session, raw_url)
  author = first_page_soup.find('div', {'class': 'detail-info'}).h2.text

  # Find the "last page" link and figure out the maximum page number
  page_links = first_page_soup.find('div', {'class': 'ui-pages'}).find_all('a')
  max_page_link = page_links[-1]['href']
  m = PAGENUM_REGEX.match(max_page_link)
  max_pagenum = int(m.group(1))

  # For a given author page, get all hrefs that link to individual books
  def get_hrefs(soup):
    return [ a['href'] for a in soup.find_all('a', {'class': 'play-pic'}) ]

  # Get the hrefs for the first page (which we already have) and compute the
  # URLs for the additional pages
  hrefs = get_hrefs(first_page_soup)
  page_urls = [ raw_url ] + \
      [ raw_url.replace('.html', '-%d.html' % (n)) for n in range (2, max_pagenum+1)]

  # Get the hrefs from the above URLs (pages 2+)
  async def page_url_to_hrefs(page_url):
    page_soup = await utils.get_soup(session, page_url)
    return get_hrefs(page_soup)

  for hrefs_list in await asyncio.gather(*map(page_url_to_hrefs, page_urls)):
    hrefs += hrefs_list

  # Compute full URLs for invidual book pages and fetch them all
  base = '%s://%s' % (url.scheme, url.netloc)
  return await asyncio.gather(
      *map(lambda href: get_book(session, base + href), hrefs))

# A link to an author page will be handled by batch-downloading all the books
# for that author. Otherwise, we treat the link as a single book.
async def get(session, url):
  if url.path.startswith('/author'):
    return await get_books_for_author(session, url)
  else:
    return [ await get_book(session, url.geturl()) ]
