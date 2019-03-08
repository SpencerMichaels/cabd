import re

from book import Book, Chapter

import utils

NAME = '我听评书网'
DOMAINS = ['www.wotingpingshu.com']

def can_handle(domain):
  return domain in DOMAINS

def get_chapter(li):
  title = li.find('div', {'class': 'psList'}).text

  dl_page_url = li.find_all('a', {'class': 'button'})[1]['href']
  soup = utils.get_soup('http:' + dl_page_url)
  url = soup.find('div', {'class': 'downsubmit'}).a['href']

  return Chapter(title=title, url=url)

def get_book(url, num_threads):
  soup = utils.get_soup(url.geturl())

  title = soup.find('span', {'class': 'a-btn-text'}).text
  art_url = soup.find('div', {'class': 'contDetail'}) \
                .find('img', {'class': 'img'})['src']
  songlist = soup.find('div', {'class': 'songlist'})
  lis = songlist.ul.find_all(recursive=False)

  print('Fetching book \"%s\"...' %s (title))
  chapters = utils.do_multi(
      get_chapter, lis,
      lambda total, chapter: utils.print_progress(len(lis), total, chapter.title), num_threads)

  return Book(title=title, art_url=art_url, chapters=chapters)

def get(url, num_threads):
  return [ get_book(url, num_threads) ]
