import json
import re
from urllib.request import urlopen

from book import Book, Chapter

import utils

NAME = '懒人听书'
DOMAINS = ['www.lanren9.com']

PAGENUM_REGEX = re.compile('^.*-([0-9]+).html$')

def can_handle(domain):
  return domain in DOMAINS

def get_chapter_url(playdata_id):
  raw_url = 'http://www.lanren9.com/xplayer/tc/tc.php?id=' + playdata_id
  with urlopen(raw_url) as response:
    body = response.read()
    return json.loads(body)['url']

# list of lists: [[ title, playdata_id, tc? ]]
def get_chapters_playdata(raw_url):
  with urlopen(raw_url) as response:
    body = response.read()
    entries = body[body.find(b'\'tudou\',[')+9:body.find(b']')].split(b',')

    def decode_entry(entry):
      sections = entry[1:-1].split(b'$', 3)
      if sections[0].startswith(b'\\'):
        return [ sections[0].decode('unicode_escape') ] + \
                 [ s.decode('ascii') for s in sections[1:] ]
      else:
        return [ str(s) for s in sections ]

    return [ decode_entry(e) for e in entries ]

def get_book(raw_url):
  soup = utils.get_soup(raw_url)

  art = soup.find('div', {'class': 'detail-pic'}).img
  title = art['alt']
  art_url = art['src']

  print(title) # TODO

  base = '/'.join(raw_url.split('/', 3)[:3])
  first_chapter_href = soup.find(id='player_1').find('a')['href']
  first_chapter_soup = utils.get_soup(base + first_chapter_href)

  playdata_path = first_chapter_soup.find(id='bo') \
                               .find('script', {'type': 'text/javascript'})['src']

  chapters_info = get_chapters_playdata(base + playdata_path)

  # Most playdata gives the audio URL directly, but a few give a 'tc' ID that
  # must be submitted to tc.php to look up the audio URL.
  if chapters_info[0][2] == 'tc':
    chapters = utils.do_multi(
        lambda info: Chapter(title=info[0], url=get_chapter_url(info[1])),
        chapters_info,
        lambda total, chapter: utils.print_progress(len(chapters_info), total, chapter.title, 1))
  else:
    chapters = [ Chapter(title=info[0], url=info[1]) for info in chapters_info ]

  return Book(title=title, art_url=art_url, chapters=chapters)

def get_books_for_author(url):
  raw_url = url.geturl()
  first_page_soup = utils.get_soup(raw_url)
  author = first_page_soup.find('div', {'class': 'detail-info'}).h2.text

  print("Fetching books for author \"%s\"..." % (author))

  page_links = first_page_soup.find('div', {'class': 'ui-pages'}).find_all('a')
  max_page_link = page_links[-1]['href']

  m = PAGENUM_REGEX.match(max_page_link)
  max_pagenum = int(m.group(1))

  get_hrefs = lambda soup: [ a['href'] for a in soup.find_all('a', {'class': 'play-pic'}) ]

  hrefs = get_hrefs(first_page_soup)
  for pagenum in range(2, max_pagenum+1):
    if pagenum > 1:
      page_url = raw_url \
          if pagenum == 1 \
          else raw_url.replace('.html', '-%d.html' % (pagenum))
    hrefs += get_hrefs(utils.get_soup(page_url))

  base = '%s://%s' % (url.scheme, url.netloc)

  books = []
  for href in hrefs:
    books.append(get_book(base + href)) # TODO

  #books = [ get_book(base + href) for href in hrefs  ]

  #books = utils.do_multi(
  #    get_book, [ base + href for href in hrefs ],
  #    lambda total, book: utils.print_progress(len(hrefs), total, book.title))

  return books

def get(url, num_threads):
  if url.path.startswith('/author'):
    return get_books_for_author(url)
  else:
    return [ get_book(url.geturl()) ]
